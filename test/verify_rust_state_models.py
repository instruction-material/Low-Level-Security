"""Validate the complete RSS5 review states, legacy boundaries and intentional compiler refusals."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import tomllib

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'RUST-05-state-models-evidence'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--proof',type=Path,required=True)
args=parser.parse_args();args.proof=args.proof.resolve()
assert not args.proof.exists()
assert os.getuid()!=0 and os.uname().sysname=='Linux' and os.uname().machine=='x86_64'
OUT=args.proof.parent;OUT.mkdir(parents=True,exist_ok=True)
commands=[]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def stop(signum,_frame):raise SystemExit(128+signum)
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)

def run(command,cwd,label,expected=0,env=None):
    entry=dict(parentTaskId='rust-state-models-evidence',parentPid=os.getpid(),command=[os.fsdecode(value) for value in command],cwd=str(cwd),
               startTime=datetime.datetime.now(datetime.UTC).isoformat(),timeoutSeconds=120)
    child=subprocess.Popen(command,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    entry['pid']=child.pid
    with (OUT/'processes.jsonl').open('a') as stream:stream.write(json.dumps(dict(entry,event='start'))+'\n')
    stdout,stderr=b'',b'';cleanup='owned process exited'
    try:stdout,stderr=child.communicate(timeout=120)
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:stdout,stderr=child.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);stdout,stderr=child.communicate()
        cleanup='owned process group terminated and reaped';raise
    finally:
        with (OUT/'processes.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(entry,event='end',endTime=datetime.datetime.now(datetime.UTC).isoformat(),exitCode=child.returncode,childProcessGroupCleanup=cleanup))+'\n')
        (OUT/(label+'.stdout.txt')).write_bytes(stdout);(OUT/(label+'.stderr.txt')).write_bytes(stderr)
    assert child.returncode==expected,(label,child.returncode,stderr.decode(errors='replace'))
    commands.append(dict(label=label,exitCode=child.returncode,stdoutSha256=sha(stdout),stderrSha256=sha(stderr)))
    return stdout,stderr


source_names=run(['git','ls-files','--','RUST-05-state-models-evidence','.github/workflows/rust-state-models.yml','test/verify_rust_state_models.py'],ROOT,'source-inventory')[0].decode().splitlines()
assert len(source_names)==len(set(source_names))==19
source={name:(ROOT/name).read_bytes() for name in source_names}
for name,raw in source.items():
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
versions={}
for name,command in [('rustc',['rustc','-Vv']),('cargo',['cargo','-V']),('rustfmt',['rustfmt','--version']),('clippy',['cargo','clippy','--version'])]:
    versions[name]=run(command,ROOT,'version-'+name)[0].decode()
assert 'release: 1.97.1\n' in versions['rustc']
USAGE=b'usage: state_model_lab [--from reviewed published reviewer] [review:name | publish | reset ...]\n'

def valid_name(role,name):
    length=len(name.encode()) if role=='starter' else len(name)
    return bool(name) and name.strip()==name and name!='-' and length<=32 and not any(ord(c)<32 or 127<=ord(c)<=159 for c in name)

def predict(role,initial,events):
    reviewed,published,name=initial
    if (not reviewed and (published or name is not None)) or (reviewed and name is None):
        return b'',b'error=invalid-legacy-state\n',65
    if name is not None and not valid_name(role,name):return b'',b'error=invalid-reviewer\n',65
    phase='published' if published else 'reviewed' if reviewed else 'draft'
    out=f'start={phase} reviewer={name if name is not None else "-"}\n'
    for step,event in enumerate(events,1):
        error=None
        if event.startswith('review:'):
            new=event.removeprefix('review:')
            if phase=='published':error='already-published'
            elif phase=='reviewed':error='already-reviewed'
            elif not valid_name(role,new):error='invalid-reviewer'
            else:phase,name='reviewed',new
        elif event=='publish':
            if phase=='draft':error='needs-review'
            elif phase=='published':error='already-published'
            else:phase='published'
        elif event=='reset':
            if phase=='published':error='published-cannot-reset'
            else:phase,name='draft',None
        else:raise AssertionError(event)
        if error:return out.encode(),('error='+error+'\n').encode(),65
        out+=f'step={step} phase={phase} reviewer={name if name is not None else "-"}\n'
    return out.encode(),b'',0

import itertools
initials=[(False,False,None),(True,False,'Alex'),(True,True,'Alex')]
sequences=[list(values) for size in range(4) for values in itertools.product(['review:Bea','review:','publish','reset'],repeat=size)]
profiles=[(initial,events) for initial in initials for events in sequences]
names=['','-',' Alex','Alex ','A B','A\nB','A\0B','a'*32,'a'*33,'é'*17,'é'*32,'é'*33,'🦀'*32,'🦀'*33,'e\u0301'*16,'e\u0301'*17]
profiles += [((False,False,None),['review:'+name]) for name in names if '\0' not in name]
profiles += [((reviewed,published,name),[]) for reviewed,published,name in itertools.product([False,True],[False,True],[None,'Alex',''])]
roles=[]
with tempfile.TemporaryDirectory(prefix='rust-state-models-evidence-') as temporary:
    work=Path(temporary)
    for role in ['starter','solution']:
        selected=PACK/role;directory=work/role;shutil.copytree(selected,directory)
        role_out=OUT/role;role_out.mkdir()
        env={**os.environ,'CARGO_TARGET_DIR':str(work/(role+'-target')),'CARGO_TERM_COLOR':'never'}
        lock=(directory/'Cargo.lock').read_bytes()
        manifest=tomllib.loads((directory/'Cargo.toml').read_text());assert manifest['package']['edition']=='2024' and 'dependencies' not in manifest
        assert tomllib.loads(lock.decode())['package']==[{'name':'state_model_lab','version':'0.1.0'}]
        run(['cargo','fmt','--all','--check'],directory,role+'-format',env=env)
        run(['rustfmt','--edition','2024','--check',*sorted(str(p.relative_to(directory)) for p in (directory/'diagnostics').glob('*.rs'))],directory,role+'-diagnostic-format',env=env)
        run(['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings'],directory,role+'-clippy',env=env)
        assert b'8 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-build',env=env)
        binary=Path(env['CARGO_TARGET_DIR'])/'debug/state_model_lab'
        expected=predict(role,initials[0],['review:Alex','publish'])
        default=run([str(binary)],directory,role+'-default',env=env);assert default==expected[:2]
        cases=[]
        for index,(initial,events) in enumerate(profiles):
            reviewed,published,name=initial
            argv=['--from',str(int(reviewed)),str(int(published)),name if name is not None else '-',*events]
            expected=predict(role,initial,events)
            assert run([str(binary),*argv],directory,f'{role}-input-{index}',expected=expected[2],env=env)==expected[:2]
            cases.append(dict(initial=initial,events=events,status=expected[2],stdoutSha256=sha(expected[0]),stderrSha256=sha(expected[1])))
        malformed=[['unknown'],['review'],['--from'],['--from','0','0'],['--from','true','0','-'],['--from','0','2','-'],['--from','0','0','-','bogus'],['review:Alex','bogus'],['publish','--from','0','0','-']]
        for index,argv in enumerate(malformed):
            assert run([str(binary),*argv],directory,f'{role}-usage-{index}',expected=64,env=env)==(b'',USAGE)
        assert run([os.fsencode(binary),b'review:\xff'],directory,role+'-invalid-utf8',expected=64,env=env)==(b'',USAGE)
        library=Path(env['CARGO_TARGET_DIR'])/'debug/libstate_model_lab.rlib'
        arguments=['--edition=2024','--extern','state_model_lab='+str(library),'-L','dependency='+str(library.parent/'deps')]
        for name,code in [('non-exhaustive','E0004'),('raw-flags','E0560' if role=='solution' else None),('exhaustive',None)]:
            target=role_out/name
            stdout,stderr=run(['rustc',*arguments,'diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name+'-build',expected=1 if code else 0,env=env)
            if code:assert not stdout and code.encode() in stderr and not target.exists()
            else:
                expected=b'error=invalid-legacy-state\n' if name=='raw-flags' else b'published\n'
                assert run([str(target)],directory,role+'-'+name+'-run',env=env)==(expected,b'')
        run(['cargo','clean'],directory,role+'-clean',env=env);assert not binary.exists()
        assert b'8 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-clean-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-clean-build',env=env)
        assert run([str(binary)],directory,role+'-clean-default',env=env)==default
        assert (directory/'Cargo.lock').read_bytes()==lock
        assert all(p.read_bytes()==(selected/p.relative_to(directory)).read_bytes() for p in directory.rglob('*') if p.is_file())
        shutil.copyfile(binary,role_out/'state_model_lab')
        roles.append(dict(role=role,inputCases=len(cases),cases=cases,unitTests=8,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,executableSha256=sha(binary.read_bytes()),starterLimitDocumented=role=='starter'))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
proof=dict(sourceRevision=os.environ.get('SOURCE_REVISION'),sourceFiles={n:sha(r) for n,r in source.items()},compilerVersions=versions,commands=commands,roles=roles,nativeExecuted=True,ordinaryUser=True,allSourceFilesUnchanged=True,temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,worksheetCompletionNotInferred=True,realAuthorizationNotClaimed=True)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(sourceFiles=19,commands=len(commands),inputCases=sum(r['inputCases'] for r in roles),compilerRefusals=3,nativeExecutables=5,temporarySourceCleanup=True)))
