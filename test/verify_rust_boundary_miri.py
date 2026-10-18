"""Interpret RSS9 library tests and the single supplied rejected case."""
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
    entry = dict(parentTaskId="rust-boundary-miri-evidence", parentPid=os.getpid(),
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


NIGHTLY="nightly-2026-07-16"
claimed=os.environ["SOURCE_REVISION"]
actual=run(["git","rev-parse","HEAD"],ROOT,"actual-source-revision")[0].decode().strip()
assert actual==claimed
source_names=run(["git","ls-files","--",PACK.name,"test/verify_rust_boundary.py","test/verify_rust_boundary_miri.py","test/verify_rust_boundary_export.py",".github/workflows/rust-boundary.yml"],ROOT,"source-inventory")[0].decode().splitlines()
assert len(source_names)==len(set(source_names))==27
source={name:(ROOT/name).read_bytes() for name in source_names}
for name,raw in source.items():
    target=OUT/"source"/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
versions={name:run(command,ROOT,name)[0].decode().strip() for name,command in [
    ("rustc-nightly",["rustc","+"+NIGHTLY,"--version","--verbose"]),
    ("cargo-nightly",["cargo","+"+NIGHTLY,"--version"]),
    ("miri",["cargo","+"+NIGHTLY,"miri","--version"]) ]}
assert "nightly" in versions["rustc-nightly"] and versions["miri"].startswith("miri ")
roles=[]
with tempfile.TemporaryDirectory(prefix="rust-boundary-miri-") as directory:
    work=Path(directory)
    for role,count in [("starter",11),("solution",17)]:
        selected=PACK/role
        project=work/role
        shutil.copytree(selected,project)
        original={p.relative_to(selected):p.read_bytes() for p in selected.rglob("*") if p.is_file()}
        env={**os.environ,"CARGO_TARGET_DIR":str(work/(role+"-miri-target")),"CARGO_NET_OFFLINE":"true","MIRIFLAGS":"-Zmiri-strict-provenance"}
        out,_=run(["cargo","+"+NIGHTLY,"miri","test","--locked","--offline","--lib"],project,role+"-miri-tests",env=env,timeout=180)
        assert f"{count} passed; 0 failed".encode() in out
        assert {p.relative_to(project):p.read_bytes() for p in project.rglob("*") if p.is_file()}==original
        roles.append(dict(role=role,unitTests=count,libraryTestsPassed=True,sourceAndLockUnchanged=True))
    bad=source[PACK.name+"/starter/diagnostics/miri-dangling.rs"]
    assert bad==source[PACK.name+"/solution/diagnostics/miri-dangling.rs"]
    project=work/"rejected"
    (project/"src").mkdir(parents=True)
    toml=b'[package]\nname = "boundary_miri_negative"\nversion = "1.0.0"\nedition = "2024"\n'
    lock=b'# This file is automatically @generated by Cargo.\n# It is not intended for manual editing.\nversion = 4\n\n[[package]]\nname = "boundary_miri_negative"\nversion = "1.0.0"\n'
    driver={"Cargo.toml":toml,"Cargo.lock":lock,"src/main.rs":bad}
    for name,raw in driver.items():
        (project/name).write_bytes(raw)
        target=OUT/"generated-driver"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(raw)
    env={**os.environ,"CARGO_TARGET_DIR":str(work/"negative-miri-target"),"CARGO_NET_OFFLINE":"true","MIRIFLAGS":"-Zmiri-strict-provenance"}
    out,err=run(["cargo","+"+NIGHTLY,"miri","run","--locked","--offline"],project,"miri-rejected-dangling",expected=1,env=env,timeout=180)
    assert out==b"" and b"Undefined Behavior" in err and b"freed" in err
    assert {p.relative_to(project):p.read_bytes() for p in project.rglob("*") if p.is_file()}=={Path(name):raw for name,raw in driver.items()}
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==8
proof=dict(sourceRevision=actual,checkedOutRevision=actual,sourceKind="checkout",nightly=NIGHTLY,
           compilerVersions=versions,miriExecuted=True,ordinaryUser=True,
           sourceFiles={name:sha(raw) for name,raw in source.items()},allSourceFilesUnchanged=True,
           temporarySourceCleanup=True,projectChecksOffline=True,
           toolchainAndSysrootSetupSeparate=True,noExternalProjectCrates=True,
           strictProvenanceFlag="-Zmiri-strict-provenance",roles=roles,
           rejectedCase=dict(sourcePath=PACK.name+"/starter/diagnostics/miri-dangling.rs",sourceSha256=sha(bad),
                             generatedDriver={name:sha(raw) for name,raw in driver.items()},
                             expectedStatus=1,actualStatus=1,undefinedBehaviorDetected=True,
                             freedAllocationDiagnostic=True,nativeExecution=False),
           worksheetCompletionNotInferred=True,allInputsTargetsAndForeignLibrariesNotProven=True,
           commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+"\n")
print(json.dumps({"accepted":True,"commands":8,"miriUnitResults":28,"expectedUBRefusals":1,"proof":str(args.proof)}))
