"""Compile the RSS10 record-hardening roles with bounded exact evidence."""
import argparse
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "RUST-10-record-hardening-capstone"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--proof", type=Path, required=True)
parser.add_argument("--source-kind", choices=["checkout","exported-workspace"], default="checkout")
args = parser.parse_args()
args.proof = args.proof.resolve()
assert not args.proof.exists()
assert os.getuid() != 0 and os.uname().sysname == "Linux" and os.uname().machine == "x86_64"
OUT = args.proof.parent
OUT.mkdir(parents=True, exist_ok=True)
commands = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stop(signum, _frame):
    raise SystemExit(128 + signum)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)


def run(command, cwd, label, expected=0, env=None, timeout=120):
    entry = dict(parentTaskId="rust-capstone-evidence", parentPid=os.getpid(),
                 command=[os.fsdecode(value) for value in command], cwd=str(cwd),
                 startTime=datetime.datetime.now(datetime.UTC).isoformat(), timeoutSeconds=timeout)
    start = time.monotonic()
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    entry["pid"] = child.pid
    with (OUT / "processes.jsonl").open("a") as stream:
        stream.write(json.dumps(dict(entry, event="start")) + "\n")
    stdout, stderr, cleanup = b"", b"", "owned process exited"
    try:
        stdout, stderr = child.communicate(timeout=timeout)
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                stdout, stderr = child.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                stdout, stderr = child.communicate()
        cleanup = "owned process group terminated and reaped"
        raise
    finally:
        with (OUT / "processes.jsonl").open("a") as stream:
            stream.write(json.dumps(dict(entry, event="end", endTime=datetime.datetime.now(datetime.UTC).isoformat(),
                                         exitCode=child.returncode, childProcessGroupCleanup=cleanup)) + "\n")
        (OUT / (label + ".stdout.txt")).write_bytes(stdout)
        (OUT / (label + ".stderr.txt")).write_bytes(stderr)
    assert child.returncode == expected, (label, child.returncode, stderr.decode(errors="replace"))
    commands.append(dict(label=label, exitCode=child.returncode, elapsedSeconds=time.monotonic()-start,
                         timeoutSeconds=timeout, stdoutSha256=sha(stdout), stderrSha256=sha(stderr)))
    return stdout, stderr


def verify_committed_bytes(actual, source):
    # Compare raw bytes with the selected commit, independently of the index,
    # clean filters, timestamps, and assume-unchanged flags.
    listing=run(["git","ls-tree","-rz","--full-tree",actual,"--",*source],ROOT,"committed-source-objects")[0]
    entries={}
    for row in listing.split(b"\0"):
        if not row:
            continue
        header,name=row.split(b"\t",1)
        mode,kind,identity=header.split()
        assert mode in [b"100644",b"100755"] and kind==b"blob"
        name=name.decode()
        assert name not in entries
        entries[name]=identity.decode()
    assert entries.keys()==source.keys(),"Committed source paths differ"
    for name,raw in source.items():
        identity=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        assert identity==entries[name],"Source bytes differ from committed revision: "+name
    return entries



import re

claimed=os.environ['SOURCE_REVISION']
assert len(claimed)==40 and all(c in '0123456789abcdef' for c in claimed)
role_names=['Cargo.toml','Cargo.lock','src/lib.rs','src/main.rs','src/fixtures.rs','observations.md']
tool_names=['test/verify_rust_capstone.py','test/verify_rust_capstone_export.py','.github/workflows/rust-capstone.yml']
expected_names=sorted([PACK.name+'/README.md']+[PACK.name+'/'+role+'/'+name for role in ['starter','solution'] for name in role_names]+tool_names)
assert len(expected_names)==16
actual=None
if args.source_kind=='checkout':
    actual=run(['git','rev-parse','HEAD'],ROOT,'actual-source-revision')[0].decode().strip()
    assert actual==claimed
    names=run(['git','ls-files','--',PACK.name,*tool_names],ROOT,'source-inventory')[0].decode().splitlines()
    assert names==expected_names
else:
    names=expected_names
for name in names:
    cursor=ROOT
    for part in Path(name).parts:
        cursor=cursor/part
        assert not cursor.is_symlink(),'Linked source entry: '+name
    assert cursor.is_file(),'Missing source entry: '+name
package_files={name.removeprefix(PACK.name+'/') for name in names if name.startswith(PACK.name+'/')}
package_dirs={Path('.')}
for name in package_files:package_dirs.update(Path(name).parents)
for relative in package_dirs:
    offset=0 if str(relative)=='.' else len(relative.parts)
    children={Path(name).parts[offset] for name in package_files if Path(name).is_relative_to(relative) and len(Path(name).parts)>offset}
    assert {p.name for p in (PACK/relative).iterdir()}==children
source={name:(ROOT/name).read_bytes() for name in names}
assert all(b'\r' not in raw for raw in source.values())
committed=verify_committed_bytes(actual,source) if args.source_kind=='checkout' else None
for name,raw in source.items():
    path=OUT/'source'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
versions={name:run(command,ROOT,name)[0].decode().strip() for name,command in [
    ('rustc',['rustc','--version','--verbose']),('cargo',['cargo','--version']),
    ('rustfmt',['rustfmt','--version']),('clippy',['cargo','clippy','--version'])]}
assert versions['rustc'].startswith('rustc 1.97.1 ')
cases={'cat':[3,99,97,116,1],'empty-label':[0,1],'over-label':[11]+[97]*11+[1],
       'short':[3,99,97],'utf8':[3,255,255,255,1],'kind':[3,99,97,116,9],
       'trailing':[3,99,97,116,1,0],'declared-max':[255],'empty':[],
       'missing-kind':[1,97],'length-only':[11],'unicode':[3,226,152,131,2],
       'exact-max':[10]+list(b'abcdefghij')+[3],'combined':[1,255,9,0]}
assert len(cases)==14


def oracle(values,role):
    data=bytes(values)
    if len(data)>12:error='too-large'
    elif not data:error='empty'
    elif data[0]==0:error='empty-label'
    elif data[0]>10:error='label-too-long'
    elif len(data)<1+data[0]:error='truncated-label'
    elif len(data)==1+data[0]:error='missing-kind'
    elif len(data)>2+data[0]:error='trailing-data'
    else:
        label=data[1:1+data[0]]
        try:label.decode('utf-8')
        except UnicodeDecodeError:error='invalid-utf8'
        else:
            if data[-1] not in [1,2,3]:error='unsupported-kind'
            else:return 'ok:'+str(data[-1])+':'+label.hex()
    return 'error:'+('unclassified' if role=='starter' and error!='too-large' else error)


corpus=[list(values) for length in range(5) for values in itertools.product([0,1,3,255],repeat=length)]
corpus.extend([length]+[value]*length+[kind] for length in range(1,11) for value in [0,97] for kind in [1,2,3])
corpus.extend(cases.values())
corpus=list(map(list,dict.fromkeys(map(tuple,corpus))))
assert 350<len(corpus)<500 and all(len(values)<=13 for values in corpus)
usage=[[],['--case'],['--help','extra'],['--case','cat','extra'],['--case','cat','extra','more'],['--unknown'],['cat'],['--case','unknown']]
USAGE=b'usage: record_hardening_lab --help | --case NAME\n'
roles=[]
with tempfile.TemporaryDirectory(prefix='rust-capstone-native-') as directory:
    work=Path(directory)
    for role,unit_count in [('starter',7),('solution',13)]:
        selected=PACK/role;project=work/role
        shutil.copytree(selected,project)
        original={p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}
        assert tomllib.loads((project/'Cargo.toml').read_text())=={'package':{'name':'record_hardening_lab','version':'1.0.0','edition':'2024'}}
        assert tomllib.loads((project/'Cargo.lock').read_text())['package']==[{'name':'record_hardening_lab','version':'1.0.0'}]
        assert len(re.findall(rb'#\[test\]\s+fn ',source[PACK.name+'/'+role+'/src/lib.rs']))==unit_count
        env={**os.environ,'CARGO_NET_OFFLINE':'true','CARGO_TARGET_DIR':str(work/(role+'-target'))}
        run(['cargo','fmt','--all','--check'],project,role+'-format',env=env)
        run(['cargo','clippy','--locked','--offline','--all-targets','--','-D','warnings'],project,role+'-clippy',env=env)
        out,_=run(['cargo','test','--locked','--offline'],project,role+'-tests',env=env)
        assert f'{unit_count} passed; 0 failed'.encode() in out
        run(['cargo','build','--locked','--offline'],project,role+'-build',env=env)
        binary=Path(env['CARGO_TARGET_DIR'])/'debug/record_hardening_lab'
        assert run([str(binary),'--help'],work,role+'-help',env=env,timeout=30)==(USAGE,b'')
        for repeat in range(2):
            for name,values in cases.items():
                result=oracle(values,role)
                expected=(b'',('error='+result.removeprefix('error:')+'\n').encode(),65) if result.startswith('error:') else (('kind='+result.split(':')[1]+' label-bytes='+str(values[0])+'\n').encode(),b'',0)
                assert run([str(binary),'--case',name],work,f'{role}-case-{name}-{repeat}',expected=expected[2],env=env,timeout=30)==expected[:2]
        for index,arguments in enumerate(usage):
            assert run([str(binary),*arguments],work,f'{role}-usage-{index}',expected=64,env=env,timeout=30)==(b'',USAGE)
        for index,arguments in enumerate([[b'--case',b'\xff'],[b'\xff']]):
            assert run([os.fsencode(binary),*arguments],work,f'{role}-utf8-{index}',expected=64,env=env,timeout=30)==(b'',USAGE)
        driver=['use record_hardening_lab::{parse_record, Record, ParseError};',
                'fn show(value: Result<Record, ParseError>) -> String { match value { Ok(record) => { let hex: String = record.label().as_bytes().iter().map(|byte| format!("{byte:02x}")).collect(); format!("ok:{}:{hex}",record.kind().value()) }, Err(error) => format!("error:{}",error.code()) } }',
                'fn main() {']
        expected_rows=[]
        for index,values in enumerate(corpus):
            driver.append('println!("case='+str(index)+' {}", show(parse_record(&['+','.join(map(str,values))+'])));')
            expected_rows.append('case='+str(index)+' '+oracle(values,role))
        driver.append('}')
        consumer=work/(role+'-consumer');(consumer/'src').mkdir(parents=True)
        generated={'Cargo.toml':'[package]\nname = "record_contract_consumer"\nversion = "1.0.0"\nedition = "2024"\n\n[dependencies]\nrecord_hardening_lab = { path = "../'+role+'" }\n',
                   'Cargo.lock':'# This file is automatically @generated by Cargo.\n# It is not intended for manual editing.\nversion = 4\n\n[[package]]\nname = "record_contract_consumer"\nversion = "1.0.0"\ndependencies = [\n "record_hardening_lab",\n]\n\n[[package]]\nname = "record_hardening_lab"\nversion = "1.0.0"\n',
                   'src/main.rs':'\n'.join(driver)+'\n'}
        for name,text in generated.items():
            (consumer/name).write_text(text)
            path=OUT/('generated-'+role)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        consumer_env={**env,'CARGO_TARGET_DIR':str(work/(role+'-consumer-target'))}
        run(['cargo','build','--locked','--offline'],consumer,role+'-consumer-build',env=consumer_env)
        out,err=run([str(Path(consumer_env['CARGO_TARGET_DIR'])/'debug/record_contract_consumer')],work,role+'-consumer-run',env=consumer_env,timeout=30)
        assert not err and out.decode().splitlines()==expected_rows
        run(['cargo','clean'],project,role+'-clean',env=env)
        out,_=run(['cargo','test','--locked','--offline'],project,role+'-clean-tests',env=env)
        assert f'{unit_count} passed; 0 failed'.encode() in out
        run(['cargo','build','--locked','--offline'],project,role+'-clean-build',env=env)
        assert run([str(binary),'--case','cat'],work,role+'-clean-valid',env=env,timeout=30)==(b'kind=1 label-bytes=3\n',b'')
        assert {p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}==original
        (OUT/role).mkdir();(OUT/role/'record_hardening_lab').write_bytes(binary.read_bytes())
        roles.append(dict(role=role,unitTests=unit_count,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,
                          cliCases=28,usageRefusals=10,consumerCases=len(corpus),consumerRows=expected_rows,
                          executableSha256=sha(binary.read_bytes()),generatedDriver={name:sha(text.encode()) for name,text in generated.items()}))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==(105 if args.source_kind=='checkout' else 102)
proof=dict(sourceRevision=actual,checkedOutRevision=actual,baseSourceRevision=claimed,sourceKind=args.source_kind,
           sourceDiscovery='git-index' if args.source_kind=='checkout' else 'fixed-filesystem',
           repositoryCIProvenanceClaimed=args.source_kind=='checkout',committedSourceObjects=committed,
           sourceFiles={name:sha(raw) for name,raw in source.items()},compilerVersions=versions,nativeExecuted=True,
           ordinaryUser=True,allSourceFilesUnchanged=True,temporarySourceCleanup=True,
           noExternalProjectCrates=True,projectChecksOffline=True,legacyPseudocodeNotExecuted=True,
           worksheetCompletionNotInferred=True,allExecutionsNotProven=True,roles=roles,corpus=corpus,commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(accepted=True,sourceKind=args.source_kind,commands=len(commands),consumerCases=len(corpus)*2,proof=str(args.proof))))
