"""Compile both RSS8 roles and retain bounded native work/lifecycle evidence."""
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
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "RUST-08-concurrency-evidence"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--proof", type=Path, required=True)
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
    entry = dict(parentTaskId="rust-concurrency-exported-evidence", parentPid=os.getpid(),
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




actual=run(['git','rev-parse','HEAD'],ROOT,'actual-source-revision')[0].decode().strip()
assert actual==os.environ['SOURCE_REVISION']
role_names=['Cargo.toml', 'Cargo.lock', 'src/lib.rs', 'src/ledger.rs', 'src/main.rs', 'observations.md', 'diagnostics/rc-not-send.rs', 'diagnostics/arc-owned.rs', 'diagnostics/cell-not-sync.rs', 'diagnostics/scoped-shared.rs']
tool_names=['test/verify_rust_concurrency.py','test/verify_rust_concurrency_export.py','.github/workflows/rust-concurrency.yml']
expected_names=sorted([PACK.name+'/README.md']+[PACK.name+'/'+role+'/'+name for role in ['starter','solution'] for name in role_names]+tool_names)
names=run(['git','ls-files','--',PACK.name,*tool_names],ROOT,'source-inventory')[0].decode().splitlines()
assert names==expected_names and len(names)==24
for name in names:
    cursor=ROOT
    for part in Path(name).parts:
        cursor=cursor/part
        assert not cursor.is_symlink()
    assert cursor.is_file()
source={name:(ROOT/name).read_bytes() for name in names}
assert all(b'\r' not in raw for raw in source.values())
committed=verify_committed_bytes(actual,source)
with tempfile.TemporaryDirectory(prefix='rust-concurrency-git-free-') as directory:
    packet=Path(directory)/'source-packet';packet.mkdir()
    assert not (packet/'.git').exists() and not (packet.parent/'.git').exists()
    for name,raw in source.items():
        path=packet/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    exported=OUT/'exported'
    _,err=run(['python3',str(packet/'test/verify_rust_concurrency.py'),'--source-kind','exported-workspace','--proof',str(exported/'proof.json')],packet,'verify-git-free-packet',timeout=300)
    assert not err
    result=json.loads((exported/'proof.json').read_text())
    assert result['sourceKind']=='exported-workspace' and result['sourceDiscovery']=='fixed-filesystem'
    assert result['sourceRevision'] is None and result['checkedOutRevision'] is None and result['committedSourceObjects'] is None
    assert result['baseSourceRevision']==actual and not result['repositoryCIProvenanceClaimed']
    assert result['sourceFiles']=={name:sha(raw) for name,raw in source.items()} and len(result['commands'])==108
    events=[json.loads(line) for line in (exported/'processes.jsonl').read_text().splitlines()]
    assert all(event['command'][0]!='git' for event in events)
    refused=OUT/'checkout-refusal'
    _,err=run(['python3',str(packet/'test/verify_rust_concurrency.py'),'--source-kind','checkout','--proof',str(refused/'proof.json')],packet,'reject-fake-checkout',expected=1,timeout=30)
    assert b'not a git repository' in err and not (refused/'proof.json').exists()
    assert not (packet/'.git').exists()
    assert {p.relative_to(packet).as_posix():p.read_bytes() for p in packet.rglob('*') if p.is_file()}==source
dirty_refusals=[]
reading=PACK/'README.md';original=reading.read_bytes()
try:
    reading.write_bytes(original+b'\nChanged worktree regression fixture.\n')
    for kind,script in [('native','verify_rust_concurrency.py'),('export','verify_rust_concurrency_export.py')]:
        refused=OUT/('dirty-checkout-'+kind)
        _,err=run(['python3',str(ROOT/'test'/script),'--proof',str(refused/'proof.json')],ROOT,'reject-dirty-'+kind,expected=1,timeout=30)
        assert b'Source bytes differ from committed revision:' in err and not (refused/'proof.json').exists()
        events=[json.loads(line) for line in (refused/'processes.jsonl').read_text().splitlines()]
        assert len(events)==6 and all(event['command'][0]=='git' for event in events)
        dirty_refusals.append(kind)
finally:
    reading.write_bytes(original)
assert not packet.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==7
proof=dict(sourceRevision=actual,checkedOutRevision=actual,sourceKind='checkout',ordinaryUser=True,
           committedSourceObjects=committed,dirtyCheckoutRefusals=dirty_refusals,
           sourceFiles={name:sha(raw) for name,raw in source.items()},allSourceFilesUnchanged=True,
           temporarySourceCleanup=True,gitFreePacketValidated=True,exportedNativeCommands=108,
           gitNotUsedInsideExportValidation=True,exportedSourceDiscovery='fixed-filesystem',
           exportedCheckoutRevision=None,exportedRepositoryCIProvenanceClaimed=False,
           checkoutModeWithoutGitRefused=True,allRoleNativeChecksRepeated=True,actualIDEIntegrationNotInferred=True,
           commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(dict(accepted=True,gitFreePacketValidated=True,exportedNativeCommands=108,dirtyCheckoutRefusals=2,proof=str(args.proof))))
