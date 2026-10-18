"""Validate the complete RSS1 roles, ownership traces and intentional compiler refusals."""
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
PACK=ROOT/'RUST-01-ownership-evidence'
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
    entry=dict(parentTaskId='rust-ownership-evidence',parentPid=os.getpid(),command=[os.fsdecode(value) for value in command],cwd=str(cwd),
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

source_names=subprocess.check_output(['git','ls-files','--','RUST-01-ownership-evidence','.github/workflows/rust-ownership.yml','test/verify_rust_ownership.py'],cwd=ROOT).decode().splitlines()
assert len(source_names)==24 and len(set(source_names))==24
source={name:(ROOT/name).read_bytes() for name in source_names}
for name,raw in source.items():
    target=OUT/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
versions={}
for name,command in [('rustc',['rustc','-Vv']),('cargo',['cargo','-V']),('rustfmt',['rustfmt','--version']),('clippy',['cargo','clippy','--version'])]:
    versions[name]=run(command,ROOT,'version-'+name)[0].decode()
assert 'release: 1.97.1\n' in versions['rustc']

labels=['packet-42','alpha','','🦀','café','a b','../local','--label','\tvalue\nnext']
state=0x0A11CE42
for index in range(33):
    chars=[]
    for _ in range(index):
        state=(state*1664525+1013904223)%2**32;chars.append(chr(1+state%127))
    labels.append(''.join(chars))
assert len(labels)==42

def expected_output(label,empty):
    initial=[] if empty else [3,1,4]
    changed=initial+[9]
    lines=['copy=7,7',f'owned={label} bytes={initial}',f'cloned={label} bytes={initial}',
           f'after-edit={label} bytes={changed}',f'snapshot={label} bytes={initial}',
           f'borrowed-label={label}',f'returned={label} bytes={changed}',
           'drop=inner-second','drop=inner-first','drop=explicit','after-explicit-drop','drop=outer']
    return ('\n'.join(lines)+'\n').encode()

roles=[]
with tempfile.TemporaryDirectory(prefix='rust-ownership-evidence-') as temporary:
    work=Path(temporary)
    for role in ['starter','solution']:
        selected=PACK/role;directory=work/role;shutil.copytree(selected,directory)
        role_out=OUT/role;role_out.mkdir()
        env={**os.environ,'CARGO_TARGET_DIR':str(work/(role+'-target')),'CARGO_TERM_COLOR':'never'}
        manifest=tomllib.loads((directory/'Cargo.toml').read_text())
        lock=(directory/'Cargo.lock').read_bytes()
        assert manifest['package']['edition']=='2024' and 'dependencies' not in manifest
        assert tomllib.loads(lock.decode())['package']==[{'name':'ownership_trace_lab','version':'0.1.0'}]
        run(['cargo','fmt','--all','--check'],directory,role+'-format',env=env)
        diagnostic_paths=sorted(str(p.relative_to(directory)) for p in (directory/'diagnostics').glob('*.rs'))
        assert len(diagnostic_paths)==6
        run(['rustfmt','--edition','2024','--check',*diagnostic_paths],directory,role+'-diagnostic-format',env=env)
        run(['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings'],directory,role+'-clippy',env=env)
        assert b'4 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-build',env=env)
        binary=Path(env['CARGO_TARGET_DIR'])/'debug/ownership_trace_lab'
        default=run([str(binary)],directory,role+'-default',env=env)
        assert default==(expected_output('packet-42',False),b'')
        for index,label in enumerate(labels):
            for mode in ['default','empty']:
                stdout,stderr=run([str(binary),label,mode],directory,f'{role}-input-{index}-{mode}',env=env)
                assert stdout==expected_output(label,mode=='empty') and not stderr
        for suffix,arguments,message in [
            ('bad-mode',['label','other'],b'usage: ownership_trace_lab [label [default|empty]]\n'),
            ('extra',['label','default','extra'],b'usage: ownership_trace_lab [label [default|empty]]\n'),
            ('invalid-utf8',[b'\xff'],b'label must be valid UTF-8\n')]:
            command=([os.fsencode(binary),*arguments] if suffix=='invalid-utf8' else [str(binary),*arguments])
            stdout,stderr=run(command,directory,role+'-'+suffix,expected=64,env=env)
            assert not stdout and stderr==message
        for name,code in [('use-after-move','E0382'),('use-after-drop','E0382'),('copy-owned','E0204')]:
            target=role_out/(name+'.rmeta')
            stdout,stderr=run(['rustc','--edition=2024','--emit=metadata','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name,expected=1,env=env)
            assert not stdout and code.encode() in stderr and not target.exists()
        fixed_hashes={}
        for name,output in [('returned-owner',b'packet-42\n'),('last-use-before-drop',b'packet-42\n'),('clone-owned',b'packet-42|packet-42!\n')]:
            target=role_out/name
            run(['rustc','--edition=2024','diagnostics/'+name+'.rs','-o',str(target)],directory,role+'-'+name+'-build',env=env)
            assert run([str(target)],directory,role+'-'+name+'-run',env=env)==(output,b'')
            fixed_hashes[name]=sha(target.read_bytes())
        run(['cargo','clean'],directory,role+'-clean',env=env);assert not binary.exists()
        assert b'4 passed; 0 failed' in run(['cargo','test','--locked','--offline'],directory,role+'-clean-tests',env=env)[0]
        run(['cargo','build','--locked','--offline'],directory,role+'-clean-build',env=env)
        assert run([str(binary)],directory,role+'-clean-default',env=env)==default
        assert (directory/'Cargo.lock').read_bytes()==lock
        assert all(p.read_bytes()==(selected/p.relative_to(directory)).read_bytes() for p in directory.rglob('*') if p.is_file())
        shutil.copyfile(binary,role_out/'ownership_trace_lab')
        roles.append(dict(role=role,inputCases=84,unitTests=4,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,
                          actualScopeTrace=['inner-second','inner-first','explicit','after-explicit-drop','outer'],
                          compilerRefusals={'use-after-move':'E0382','use-after-drop':'E0382','copy-owned':'E0204'},
                          fixedExecutableSha256=fixed_hashes,executableSha256=sha(binary.read_bytes())))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==216,len(commands)
proof=dict(sourceRevision=os.environ.get('SOURCE_REVISION'),sourceFiles={n:sha(r) for n,r in source.items()},
           compilerVersions=versions,commands=commands,roles=roles,nativeExecuted=True,ordinaryUser=True,
           allSourceFilesUnchanged=True,temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,
           worksheetCompletionNotInferred=True,allocationOrTimingClaimsNotInferred=True)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(sourceFiles=24,commands=len(commands),inputCases=168,compilerRefusals=6,fixedPrograms=6,temporarySourceCleanup=True)))
