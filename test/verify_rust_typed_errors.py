"""Validate the complete RSS3 numeric and typed roles and intentional compiler refusals."""
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
PACK=ROOT/'RUST-03-typed-errors-evidence'
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
    entry=dict(parentTaskId='rust-typed-errors-evidence',parentPid=os.getpid(),command=[os.fsdecode(value) for value in command],cwd=str(cwd),
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


source_names=run(['git','ls-files','--','RUST-03-typed-errors-evidence','.github/workflows/rust-typed-errors.yml','test/verify_rust_typed_errors.py'],ROOT,'source-inventory')[0].decode().splitlines()
assert len(source_names)==len(set(source_names))==26
source={name:(ROOT/name).read_bytes() for name in source_names}
for name,raw in source.items():
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
versions={}
for name,command in [('rustc',['rustc','-Vv']),('cargo',['cargo','-V']),('rustfmt',['rustfmt','--version']),('clippy',['cargo','clippy','--version'])]:
    versions[name]=run(command,ROOT,'version-'+name)[0].decode()
assert 'release: 1.97.1\n' in versions['rustc']
records=['A:0','A:1','A:17','A:65535','A:65534','A:00017','A:00000','A:0000065535','A:000000','A:32768','A:32767','A:256']
state=0x0E220042
for index in range(30):
    state=(state*1664525+1013904223)%2**32
    value=state%65536
    records.append('A:'+str(value).zfill(1+index%8))
assert len(records)==42
bad=['','A17',':17','B:17','a:17','A:','A:-1','A:+1','A:1.0','A:١٧','A:17 ','A:17x','A:17:2','A:65536','A:99999','A:'+'9'*96,'A:PRIVATE_MARKER','\tA:17',' A:17','A: 17']
assert len(bad)==20
actions={'missing-separator':'add-separator','unknown-kind':'choose-A','missing-value':'supply-value','invalid-number':'use-ASCII-digits','value-out-of-range':'use-u16-range'}
def predict(text):
    if ':' not in text:code='missing-separator'
    else:
        kind,value=text.split(':',1)
        if kind!='A':code='unknown-kind'
        elif not value:code='missing-value'
        elif any(ch not in '0123456789' for ch in value):code='invalid-number'
        elif int(value)>65535:code='value-out-of-range'
        else:return (f'record=Alpha value={int(value)}\n'.encode(),b'',0)
    return b'',f'error={code} action={actions[code]}\n'.encode(),65
def scan_prediction(rows):
    for row in rows:
        if row:return predict(row)
    return b'record=absent\n',b'',0
roles=[]
with tempfile.TemporaryDirectory(prefix='rust-typed-errors-evidence-') as temporary:
    work=Path(temporary)
    for role in ['starter','solution']:
        selected=PACK/role;directory=work/role;shutil.copytree(selected,directory)
        role_out=OUT/role;role_out.mkdir()
        env={**os.environ,'CARGO_TARGET_DIR':str(work/(role+'-target')),'CARGO_TERM_COLOR':'never'}
        lock=(directory/'Cargo.lock').read_bytes()
        manifest=tomllib.loads((directory/'Cargo.toml').read_text())
        assert manifest['package']['edition']=='2024' and 'dependencies' not in manifest
        assert tomllib.loads(lock.decode())['package']==[{'name':'typed_record_lab','version':'0.1.0'}]
        run(['cargo','fmt','--all','--check'],directory,role+'-format',env=env)
        paths=sorted(str(p.relative_to(directory)) for p in (directory/'diagnostics').glob('*.rs'));assert len(paths)==6
        run(['rustfmt','--edition','2024','--check',*paths],directory,role+'-diagnostic-format',env=env)
        run(['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings'],directory,role+'-clippy',env=env)
        assert b'8 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-build',env=env)
        binary=Path(env['CARGO_TARGET_DIR'])/'debug/typed_record_lab'
        default=run([str(binary)],directory,role+'-default',env=env);assert default==predict('A:17')[:2]
        for index,text in enumerate(records):
            for mode in ['record','scan']:
                argv=['--record',text] if mode=='record' else ['--scan','',text]
                expected=predict(text)
                assert run([str(binary),*argv],directory,f'{role}-input-{index}-{mode}',env=env)==expected[:2]
        for index,text in enumerate(bad):
            for mode in ['record','scan']:
                argv=['--record',text] if mode=='record' else ['--scan','',text]
                expected=predict(text) if mode=='record' else scan_prediction(['',text])
                assert run([str(binary),*argv],directory,f'{role}-bad-{index}-{mode}',expected=expected[2],env=env)==expected[:2]
        for index,rows in enumerate([[],[''],['',''],['']*8]):
            assert run([str(binary),'--scan',*rows],directory,f'{role}-absence-{index}',env=env)==scan_prediction(rows)[:2]
        for name,rows in [('success-first',['A:17','B:0']),('error-first',['A:','A:17'])]:
            expected=scan_prediction(rows)
            assert run([str(binary),'--scan',*rows],directory,role+'-'+name,expected=expected[2],env=env)==expected[:2]
        for index,argv in enumerate([['--other'],['--record'],['--record','A:17','extra'],['--scan',*(['']*9)]]):
            assert run([str(binary),*argv],directory,f'{role}-usage-{index}',expected=64,env=env)==(b'',b'usage: typed_record_lab [--record record | --scan [record ...]]\n')
        for name,argv in [('invalid-record',[b'--record',b'\xff']),('invalid-mode',[b'\xff'])]:
            assert run([os.fsencode(binary),*argv],directory,role+'-'+name,expected=64,env=env)==(b'',b'arguments must be valid UTF-8\n')
        for name,code in [('missing-match','E0004'),('option-question-mark','E0277'),('sentinel-result','E0308')]:
            target=role_out/(name+'.rmeta')
            stdout,stderr=run(['rustc','--edition=2024','--emit=metadata','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name,expected=1,env=env)
            assert not stdout and code.encode() in stderr and not target.exists()
        hashes={}
        for name,output in [('exhaustive-match',b'missing-separator\nunknown-kind\nmissing-value\ninvalid-number\nvalue-out-of-range\n'),('option-to-result',b'Err("missing-kind")\n'),('typed-result',b'Err("missing-value")\n')]:
            target=role_out/name
            run(['rustc','--edition=2024','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name+'-build',env=env)
            assert run([str(target)],directory,role+'-'+name+'-run',env=env)==(output,b'')
            hashes[name]=sha(target.read_bytes())
        run(['cargo','clean'],directory,role+'-clean',env=env);assert not binary.exists()
        assert b'8 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-clean-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-clean-build',env=env)
        assert run([str(binary)],directory,role+'-clean-default',env=env)==default
        assert (directory/'Cargo.lock').read_bytes()==lock
        assert all(p.read_bytes()==(selected/p.relative_to(directory)).read_bytes() for p in directory.rglob('*') if p.is_file())
        shutil.copyfile(binary,role_out/'typed_record_lab')
        roles.append(dict(role=role,inputCases=84,unitTests=8,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,all65536ValuesTested=True,numericBaselineOrTypedTarget='numeric baseline' if role=='starter' else 'typed target',fixedExecutableSha256=hashes,executableSha256=sha(binary.read_bytes())))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==315,len(commands)
proof=dict(sourceRevision=os.environ.get('SOURCE_REVISION'),sourceFiles={n:sha(r) for n,r in source.items()},compilerVersions=versions,commands=commands,roles=roles,nativeExecuted=True,ordinaryUser=True,allSourceFilesUnchanged=True,temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,worksheetCompletionNotInferred=True,productionResourceLimitsNotInferred=True)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(sourceFiles=26,commands=len(commands),validInputCases=168,compilerRefusals=6,fixedPrograms=6,temporarySourceCleanup=True)))
