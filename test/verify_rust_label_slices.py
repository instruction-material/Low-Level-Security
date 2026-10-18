"""Validate the complete RSS4 label and range roles and intentional compiler refusals."""
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
PACK=ROOT/'RUST-04-label-slices-evidence'
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
    entry=dict(parentTaskId='rust-label-slices-evidence',parentPid=os.getpid(),command=[os.fsdecode(value) for value in command],cwd=str(cwd),
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


source_names=run(['git','ls-files','--','RUST-04-label-slices-evidence','.github/workflows/rust-label-slices.yml','test/verify_rust_label_slices.py'],ROOT,'source-inventory')[0].decode().splitlines()
assert len(source_names)==len(set(source_names))==30
source={name:(ROOT/name).read_bytes() for name in source_names}
for name,raw in source.items():
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
versions={}
for name,command in [('rustc',['rustc','-Vv']),('cargo',['cargo','-V']),('rustfmt',['rustfmt','--version']),('clippy',['cargo','clippy','--version'])]:
    versions[name]=run(command,ROOT,'version-'+name)[0].decode()
assert 'release: 1.97.1\n' in versions['rustc']
texts=['','packet-42!','a🦀bc','é','e\u0301','é🦀A','--FLAG','  A_B!','A\tB\nC','中-A-9','ßé🦀','0123456789','A-Z-a-z','\x7f']
texts=[t.replace('\u0301','\u0301').replace('\t','\t').replace('\n','\n').replace('\x7f','\x7f') for t in texts]
def predict(role,mode,text,start=None,end=None):
    if mode=='sanitize':
        clean=text if role=='starter' else ''.join(ch for ch in text if ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-')
        return ('label='+clean+'\n').encode(),b'',0
    raw=text.encode();length=len(text) if mode=='chars' else len(raw)
    if start>end:code='range-reversed'
    elif end>length:code='out-of-bounds'
    elif mode=='bytes':return ('bytes='+str(list(raw[start:end]))+'\n').encode(),b'',0
    else:
        try:selected=text[start:end] if mode=='chars' else raw[start:end].decode()
        except UnicodeDecodeError:code='not-character-boundary'
        else:
            # An empty byte interval must still lie on a scalar boundary.
            boundaries={0};offset=0
            for character in text:offset+=len(character.encode());boundaries.add(offset)
            if mode=='window' and (start not in boundaries or end not in boundaries):code='not-character-boundary'
            else:return f'window={selected} bytes={len(selected.encode())} scalars={len(selected)}\n'.encode(),b'',0
    return b'',('error='+code+'\n').encode(),65
roles=[]
with tempfile.TemporaryDirectory(prefix='rust-label-slices-evidence-') as temporary:
    work=Path(temporary)
    for role in ['starter','solution']:
        selected=PACK/role;directory=work/role;shutil.copytree(selected,directory)
        role_out=OUT/role;role_out.mkdir()
        env={**os.environ,'CARGO_TARGET_DIR':str(work/(role+'-target')),'CARGO_TERM_COLOR':'never','RUST_BACKTRACE':'0'}
        lock=(directory/'Cargo.lock').read_bytes()
        manifest=tomllib.loads((directory/'Cargo.toml').read_text());assert manifest['package']['edition']=='2024' and 'dependencies' not in manifest
        assert tomllib.loads(lock.decode())['package']==[{'name':'label_slice_lab','version':'0.1.0'}]
        run(['cargo','fmt','--all','--check'],directory,role+'-format',env=env)
        diagnostics=sorted(str(p.relative_to(directory)) for p in (directory/'diagnostics').glob('*.rs'));assert len(diagnostics)==8
        run(['rustfmt','--edition','2024','--check',*diagnostics],directory,role+'-diagnostic-format',env=env)
        run(['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings'],directory,role+'-clippy',env=env)
        assert b'8 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-build',env=env)
        binary=Path(env['CARGO_TARGET_DIR'])/'debug/label_slice_lab'
        default=run([str(binary)],directory,role+'-default',env=env);assert default==predict(role,'sanitize','packet-42!')[:2]
        cases=[]
        for text in texts:
            cases.append(('sanitize',text,None,None))
        for text in texts[:6]:
            for mode in ['window','bytes','chars']:
                size=len(text) if mode=='chars' else len(text.encode())
                pairs={(0,0),(0,size),(size,size),(size+1,size+1),(1,0),(0,size+1),(1,2),(2,3)}
                cases.extend((mode,text,start,end) for start,end in sorted(pairs))
        for index,(mode,text,start,end) in enumerate(cases):
            argv=['--sanitize',text] if mode=='sanitize' else ['--'+mode,text,str(start),str(end)]
            expected=predict(role,mode,text,start,end)
            assert run([str(binary),*argv],directory,f'{role}-input-{index}',expected=expected[2],env=env)==expected[:2]
        usage=b'usage: label_slice_lab [--sanitize text | --window text start end | --bytes text start end | --chars text start end]\n'
        for index,argv in enumerate([['--other'],['--sanitize'],['--window','a','0'],['--bytes','a','0','1','extra']]):
            assert run([str(binary),*argv],directory,f'{role}-usage-{index}',expected=64,env=env)==(b'',usage)
        for index,value in enumerate(['','-1','+1',' 1','١','1.0','18446744073709551616']):
            assert run([str(binary),'--window','a',value,'1'],directory,f'{role}-bad-index-{index}',expected=64,env=env)==(b'',b'indices must be ASCII decimal usize values\n')
        assert run([os.fsencode(binary),b'--sanitize',b'\xff'],directory,role+'-invalid-utf8',expected=64,env=env)==(b'',b'arguments must be valid UTF-8\n')
        target=role_out/'string-index.rmeta'
        stdout,stderr=run(['rustc','--edition=2024','--emit=metadata','diagnostics/string-index.rs','-o',str(target)],directory,role+'-string-index',expected=1,env=env)
        assert not stdout and b'E0277' in stderr and not target.exists()
        hashes={}
        for name in ['byte-out-of-bounds','non-boundary-slice','reversed-range','scalar-index','checked-byte','checked-string','checked-range']:
            target=role_out/name
            run(['rustc','--edition=2024','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name+'-build',env=env)
            refused=name in ['byte-out-of-bounds','non-boundary-slice','reversed-range']
            out,err=run([str(target)],directory,role+'-'+name+'-run',expected=101 if refused else 0,env=env)
            if refused:assert not out and b'panicked' in err
            else:assert not err and out==("Some('🦀')\n".encode() if name=='scalar-index' else b'None\n')
            hashes[name]=sha(target.read_bytes())
        run(['cargo','clean'],directory,role+'-clean',env=env);assert not binary.exists()
        assert b'8 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-clean-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-clean-build',env=env)
        assert run([str(binary)],directory,role+'-clean-default',env=env)==default
        assert (directory/'Cargo.lock').read_bytes()==lock
        assert all(p.read_bytes()==(selected/p.relative_to(directory)).read_bytes() for p in directory.rglob('*') if p.is_file())
        shutil.copyfile(binary,role_out/'label_slice_lab')
        roles.append(dict(role=role,inputCases=len(cases),unitTests=8,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,unfinishedIdentityOrCompletedFilter='unfinished identity' if role=='starter' else 'completed ASCII filter',fixedAndPanicExecutableSha256=hashes,executableSha256=sha(binary.read_bytes())))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
proof=dict(sourceRevision=os.environ.get('SOURCE_REVISION'),sourceFiles={n:sha(r) for n,r in source.items()},compilerVersions=versions,commands=commands,roles=roles,nativeExecuted=True,ordinaryUser=True,allSourceFilesUnchanged=True,temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,worksheetCompletionNotInferred=True,graphemeSegmentationNotClaimed=True)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(sourceFiles=30,commands=len(commands),inputCases=sum(r['inputCases'] for r in roles),compilerRefusals=2,intentionalPanics=6,temporarySourceCleanup=True)))
