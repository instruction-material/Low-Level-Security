"""Validate the complete RSS2 owned and borrowed roles and intentional compiler refusals."""
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
PACK=ROOT/'RUST-02-borrowing-evidence'
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
    entry=dict(parentTaskId='rust-borrowing-evidence',parentPid=os.getpid(),command=[os.fsdecode(value) for value in command],cwd=str(cwd),
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

source_names=run(['git','ls-files','--','RUST-02-borrowing-evidence','.github/workflows/rust-borrowing.yml','test/verify_rust_borrowing.py'],ROOT,'source-inventory')[0].decode().splitlines()
assert len(source_names)==28 and len(set(source_names))==28
source={name:(ROOT/name).read_bytes() for name in source_names}
for name,raw in source.items():
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
versions={}
for name,command in [('rustc',['rustc','-Vv']),('cargo',['cargo','-V']),('rustfmt',['rustfmt','--version']),('clippy',['cargo','clippy','--version'])]:
    versions[name]=run(command,ROOT,'version-'+name)[0].decode()
assert 'release: 1.97.1\n' in versions['rustc']

pairs=[('ALPHA','ADMIN'),('',''),('ÉA','ß'),('Crab🦀','STUDENT'),('A B','  '),('../LOCAL','--FLAG'),('NAME=VALUE','ROLE=VALUE'),('\tX\nY','TEST'),('ALPHA','Bravo')]
state=0x0B022042
for index in range(33):
    fields=[]
    for size in [index,32-index]:
        chars=[]
        for _ in range(size):
            state=(state*1664525+1013904223)%2**32
            value=1+state%127
            chars.append(chr(58 if value==59 else value))
        fields.append(''.join(chars))
    pairs.append(tuple(fields))
labels=['name='+name+';role='+role for name,role in pairs]
assert len(labels)==42

def expected_output(record,empty):
    name,role=record.removeprefix('name=').split(';role=',1)
    table=str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')
    left,right=name.translate(table),role.translate(table)
    selected=left if len(left.encode())>=len(right.encode()) else right
    counters=[] if empty else [2,3,13,14]
    return (f'shared={name}|{role}\nnormalized=name={left};role={right}\nselected={selected}\nhalves={counters}\nowned-after-drop={left}\n').encode()

roles=[]
with tempfile.TemporaryDirectory(prefix='rust-borrowing-evidence-') as temporary:
    work=Path(temporary)
    for role in ['starter','solution']:
        selected=PACK/role;directory=work/role;shutil.copytree(selected,directory)
        role_out=OUT/role;role_out.mkdir()
        env={**os.environ,'CARGO_TARGET_DIR':str(work/(role+'-target')),'CARGO_TERM_COLOR':'never'}
        manifest=tomllib.loads((directory/'Cargo.toml').read_text())
        lock=(directory/'Cargo.lock').read_bytes()
        assert manifest['package']['edition']=='2024' and 'dependencies' not in manifest
        assert tomllib.loads(lock.decode())['package']==[{'name':'borrowed_record_lab','version':'0.1.0'}]
        run(['cargo','fmt','--all','--check'],directory,role+'-format',env=env)
        diagnostic_paths=sorted(str(p.relative_to(directory)) for p in (directory/'diagnostics').glob('*.rs'))
        assert len(diagnostic_paths)==8
        run(['rustfmt','--edition','2024','--check',*diagnostic_paths],directory,role+'-diagnostic-format',env=env)
        run(['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings'],directory,role+'-clippy',env=env)
        assert b'7 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-build',env=env)
        binary=Path(env['CARGO_TARGET_DIR'])/'debug/borrowed_record_lab'
        default=run([str(binary)],directory,role+'-default',env=env)
        assert default==(expected_output('name=ALPHA;role=ADMIN',False),b'')
        for index,label in enumerate(labels):
            for mode in ['full','empty']:
                stdout,stderr=run([str(binary),label,mode],directory,f'{role}-input-{index}-{mode}',env=env)
                assert stdout==expected_output(label,mode=='empty') and not stderr
        for suffix,arguments,message in [
            ('bad-mode',['label','other'],b'usage: borrowed_record_lab [record [full|empty]]\n'),
            ('extra',['label','full','extra'],b'usage: borrowed_record_lab [record [full|empty]]\n'),
            ('invalid-utf8',[b'\xff'],b'record must be valid UTF-8\n')]:
            command=([os.fsencode(binary),*arguments] if suffix=='invalid-utf8' else [str(binary),*arguments])
            stdout,stderr=run(command,directory,role+'-'+suffix,expected=64,env=env)
            assert not stdout and stderr==message
        for index,record in enumerate(['name=alpha','name=alpha;group=admin','name=a;role=b;extra=c','NAME=a;role=b']):
            stdout,stderr=run([str(binary),record],directory,f'{role}-schema-{index}',expected=65,env=env)
            assert not stdout and stderr==b'expected name=<text>;role=<text> with exactly two fields\n'
        for name,code in [('shared-and-mutable','E0502'),('two-mutable','E0499'),('escaped-local','E0515'),('missing-lifetime','E0106')]:
            target=role_out/(name+'.rmeta')
            stdout,stderr=run(['rustc','--edition=2024','--emit=metadata','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name,expected=1,env=env)
            assert not stdout and code.encode() in stderr and not target.exists()
        fixed_hashes={}
        for name,output in [('last-use-before-mutation',b'ALPHA\nalpha\n'),('split-borrows',b'[2, 12]\n'),('owned-result',b'alpha\n'),('related-lifetimes',b'student\n')]:
            target=role_out/name
            run(['rustc','--edition=2024','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name+'-build',env=env)
            assert run([str(target)],directory,role+'-'+name+'-run',env=env)==(output,b'')
            fixed_hashes[name]=sha(target.read_bytes())
        run(['cargo','clean'],directory,role+'-clean',env=env);assert not binary.exists()
        assert b'7 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-clean-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-clean-build',env=env)
        assert run([str(binary)],directory,role+'-clean-default',env=env)==default
        assert (directory/'Cargo.lock').read_bytes()==lock
        assert all(p.read_bytes()==(selected/p.relative_to(directory)).read_bytes() for p in directory.rglob('*') if p.is_file())
        shutil.copyfile(binary,role_out/'borrowed_record_lab')
        roles.append(dict(role=role,inputCases=84,unitTests=7,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,
                          sourceRoleGoal='owned baseline' if role=='starter' else 'borrowed target',
                          compilerRefusals={'shared-and-mutable':'E0502','two-mutable':'E0499','escaped-local':'E0515','missing-lifetime':'E0106'},
                          fixedExecutableSha256=fixed_hashes,executableSha256=sha(binary.read_bytes())))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==231,len(commands)
proof=dict(sourceRevision=os.environ.get('SOURCE_REVISION'),sourceFiles={n:sha(r) for n,r in source.items()},
           compilerVersions=versions,commands=commands,roles=roles,nativeExecuted=True,ordinaryUser=True,
           allSourceFilesUnchanged=True,temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,
           worksheetCompletionNotInferred=True,allocationOrTimingClaimsNotInferred=True)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(sourceFiles=28,commands=len(commands),inputCases=168,compilerRefusals=8,fixedPrograms=8,temporarySourceCleanup=True)))
