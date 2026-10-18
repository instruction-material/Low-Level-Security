"""Verify the Git-free exported source context and fail-closed checkout context."""
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
PACK = ROOT / "RUST-09-boundary-review-evidence"
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
    entry = dict(parentTaskId="rust-boundary-exported-evidence", parentPid=os.getpid(),
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


actual=run(["git","rev-parse","HEAD"],ROOT,"actual-source-revision")[0].decode().strip()
assert actual==os.environ["SOURCE_REVISION"]
names=run(["git","ls-files","--",PACK.name,"test/verify_rust_boundary.py","test/verify_rust_boundary_miri.py","test/verify_rust_boundary_export.py",".github/workflows/rust-boundary.yml"],ROOT,"source-inventory")[0].decode().splitlines()
assert len(names)==len(set(names))==27
source={name:(ROOT/name).read_bytes() for name in names}
with tempfile.TemporaryDirectory(prefix="rust-boundary-git-free-") as directory:
    packet=Path(directory)/"source-packet"
    packet.mkdir()
    assert not (packet/".git").exists()
    assert not (packet.parent/".git").exists()
    for name,raw in source.items():
        target=packet/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
    exported=OUT/"exported"
    out,err=run(["python3",str(packet/"test/verify_rust_boundary.py"),"--source-kind","exported-workspace","--proof",str(exported/"proof.json")],packet,"verify-git-free-packet",timeout=300)
    assert err==b""
    result=json.loads((exported/"proof.json").read_text())
    assert result["sourceKind"]=="exported-workspace" and result["sourceDiscovery"]=="fixed-filesystem"
    assert result["checkedOutRevision"] is None and result["sourceRevision"] is None
    assert result["baseSourceRevision"]==actual and not result["repositoryCIProvenanceClaimed"]
    assert result["sourceFiles"]=={name:sha(raw) for name,raw in source.items()}
    assert len(result["commands"])==84 and all(command["label"] not in ["actual-source-revision","source-inventory"] for command in result["commands"])
    events=[json.loads(line) for line in (exported/"processes.jsonl").read_text().splitlines()]
    assert all(event["command"][0]!="git" for event in events)
    refused=OUT/"checkout-refusal"
    out,err=run(["python3",str(packet/"test/verify_rust_boundary.py"),"--source-kind","checkout","--proof",str(refused/"proof.json")],packet,"reject-fake-checkout",expected=1,timeout=30)
    assert b"not a git repository" in err and not (refused/"proof.json").exists()
    assert not (packet/".git").exists()
    assert {p.relative_to(packet).as_posix():p.read_bytes() for p in packet.rglob("*") if p.is_file()}==source
assert not packet.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==4
proof=dict(sourceRevision=actual,checkedOutRevision=actual,sourceKind="checkout",ordinaryUser=True,
           gitFreePacketValidated=True,exportedNativeCommands=84,gitNotUsedInsideExportValidation=True,
           exportedSourceDiscovery="fixed-filesystem",exportedCheckoutRevision=None,
           exportedRepositoryCIProvenanceClaimed=False,checkoutModeWithoutGitRefused=True,
           sourceFiles={name:sha(raw) for name,raw in source.items()},allSourceFilesUnchanged=True,
           temporarySourceCleanup=True,allRoleNativeChecksRepeated=True,actualIDEIntegrationNotInferred=True,
           commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+"\n")
print(json.dumps({"accepted":True,"gitFreePacketValidated":True,"exportedNativeCommands":84,"fakeCheckoutRefused":True,"proof":str(args.proof)}))
