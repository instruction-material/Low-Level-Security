"""Compile both RSS9 roles and retain bounded native work/lifecycle evidence."""
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
PACK = ROOT / "RUST-09-boundary-review-evidence"
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
    entry = dict(parentTaskId="rust-boundary-evidence", parentPid=os.getpid(),
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


claimed=os.environ["SOURCE_REVISION"]
actual=None
if args.source_kind=="checkout":
    actual=run(["git","rev-parse","HEAD"],ROOT,"actual-source-revision")[0].decode().strip()
    assert actual==claimed,"Checked-out revision differs from claimed source"
source_names=run(["git","ls-files","--",PACK.name,"test/verify_rust_boundary.py","test/verify_rust_boundary_miri.py",".github/workflows/rust-boundary.yml"],ROOT,"source-inventory")[0].decode().splitlines()
assert len(source_names)==len(set(source_names))==26
source={name:(ROOT/name).read_bytes() for name in source_names}
assert all(b"\r" not in raw for raw in source.values())
for name,raw in source.items():
    target=OUT/"source"/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
versions={name:run(command,ROOT,name)[0].decode().strip() for name,command in [
    ("rustc",["rustc","--version","--verbose"]),("cargo",["cargo","--version"]),
    ("rustfmt",["rustfmt","--version"]),("clippy",["cargo","clippy","--version"]) ]}
assert versions["rustc"].startswith("rustc 1.97.1 ")
USAGE=b"usage: boundary_review_lab --help | --case NAME\n"
cases={"empty":(b"length=0 checksum=0\n",b"",0),"valid":(b"length=2 checksum=24\n",b"",0),
       "cap":(b"length=8 checksum=2040\n",b"",0),"over":(b"",b"error=too-large\n",65)}
usage=[[],["--case"],["--help","extra"],["--case","valid","extra"],["--case","valid","extra","more"],["--unknown"],["valid"],["--case","unknown"]]
corpus=[list(values) for length in range(5) for values in itertools.product([0,1,255],repeat=length)]
corpus.extend([([value]*length) for length in range(5,10) for value in [0,1,255]])
assert len(corpus)==136
consumer=["use boundary_review_lab::{checksum, safe_checksum};", "fn show(value: Result<u32,boundary_review_lab::BoundaryError>) -> String { match value { Ok(n)=>format!(\"ok:{n}\"), Err(error)=>format!(\"error:{}\",error.code()) } }", "fn main() {"]
for index,values in enumerate(corpus):
    literal=",".join(map(str,values))
    consumer.append(f'let bytes: &[u8]=&[{literal}]; println!("case={index} checksum={{}} safe={{}}",show(checksum(bytes)),show(safe_checksum(bytes)));')
consumer.append("}")
roles=[]
with tempfile.TemporaryDirectory(prefix="rust-boundary-native-") as directory:
    work=Path(directory)
    for role,unit_tests in [("starter",11),("solution",17)]:
        selected=PACK/role
        project=work/role
        shutil.copytree(selected,project)
        original={p.relative_to(selected):p.read_bytes() for p in selected.rglob("*") if p.is_file()}
        lock=(project/"Cargo.lock").read_bytes()
        assert tomllib.loads((project/"Cargo.toml").read_text())=={"package":{"name":"boundary_review_lab","version":"1.0.0","edition":"2024"}}
        assert tomllib.loads(lock.decode())["package"]==[{"name":"boundary_review_lab","version":"1.0.0"}]
        env={**os.environ,"CARGO_TARGET_DIR":str(work/(role+"-target")),"CARGO_NET_OFFLINE":"true"}
        run(["cargo","fmt","--all","--check"],project,role+"-format",env=env)
        diagnostics=sorted((project/"diagnostics").glob("*.rs"))
        assert len(diagnostics)==5
        run(["rustfmt","--edition","2024","--check",*map(str,diagnostics)],project,role+"-diagnostic-format",env=env)
        run(["cargo","clippy","--locked","--offline","--all-targets","--","-D","warnings"],project,role+"-clippy",env=env)
        assert f"{unit_tests} passed; 0 failed".encode() in run(["cargo","test","--locked","--offline"],project,role+"-tests",env=env)[0]
        run(["cargo","build","--locked","--offline"],project,role+"-build",env=env)
        binary=Path(env["CARGO_TARGET_DIR"])/"debug/boundary_review_lab"
        assert run([str(binary),"--help"],work,role+"-help",env=env,timeout=30)==(USAGE,b"")
        for repeat in range(3):
            for case,expected in cases.items():
                assert run([str(binary),"--case",case],work,f"{role}-case-{case}-{repeat}",expected=expected[2],env=env,timeout=30)==expected[:2]
        for index,arguments in enumerate(usage):
            assert run([str(binary),*arguments],work,f"{role}-usage-{index}",expected=64,env=env,timeout=30)==(b"",USAGE)
        for index,arguments in enumerate([[b"--case",b"\xff"],[b"\xff"]]):
            assert run([os.fsencode(binary),*arguments],work,f"{role}-utf8-{index}",expected=64,env=env,timeout=30)==(b"",USAGE)
        for diagnostic in diagnostics:
            if diagnostic.name=="miri-dangling.rs":
                continue
            rejected=diagnostic.stem in {"unsafe-call","unsafe-body"}
            target=work/(role+"-"+diagnostic.stem)
            out,err=run(["rustc","--edition=2024","--error-format=json",str(diagnostic),"-o",str(target)],work,role+"-"+diagnostic.stem+"-compile",expected=int(rejected),env=env)
            assert out==b""
            if rejected:
                messages=[json.loads(line) for line in err.splitlines()]
                assert any(isinstance(message.get("code"),dict) and message["code"]["code"]=="E0133" for message in messages)
                assert not target.exists()
            else:
                assert err==b""
                assert run([str(target)],work,role+"-"+diagnostic.stem+"-run",env=env,timeout=30)==(b"7\n",b"")
        probe=work/(role+"-consumer.rs")
        probe.write_text("\n".join(consumer)+"\n")
        executable=work/(role+"-consumer")
        run(["rustc","--edition=2024","--crate-name","consumer",str(probe),"--extern","boundary_review_lab="+str(Path(env["CARGO_TARGET_DIR"])/"debug/libboundary_review_lab.rlib"),"-L","dependency="+str(Path(env["CARGO_TARGET_DIR"])/"debug/deps"),"-o",str(executable)],work,role+"-consumer-compile",env=env)
        out,err=run([str(executable)],work,role+"-consumer-run",env=env,timeout=30)
        assert err==b""
        expected=[]
        for index,values in enumerate(corpus):
            result="error:too-large" if len(values)>8 else "ok:"+str(sum(values))
            expected.append(f"case={index} checksum={result} safe={result}")
        assert out.decode().splitlines()==expected
        run(["cargo","clean"],project,role+"-clean",env=env)
        assert not binary.exists()
        assert f"{unit_tests} passed; 0 failed".encode() in run(["cargo","test","--locked","--offline"],project,role+"-clean-tests",env=env)[0]
        run(["cargo","build","--locked","--offline"],project,role+"-clean-build",env=env)
        assert run([str(binary),"--case","valid"],work,role+"-clean-valid",env=env,timeout=30)==cases["valid"][:2]
        assert {p.relative_to(project):p.read_bytes() for p in project.rglob("*") if p.is_file()}==original
        saved=OUT/role
        saved.mkdir()
        shutil.copyfile(binary,saved/"boundary_review_lab")
        roles.append(dict(role=role,unitTests=unit_tests,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,
                          consumerCases=len(corpus),apiResults=len(corpus)*2,cliCases=12,usageRefusals=10,
                          compilerRefusals=2,consumerRows=expected,executableSha256=sha(binary.read_bytes())))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==(86 if args.source_kind=="checkout" else 85)
proof=dict(sourceKind=args.source_kind,sourceRevision=actual,checkedOutRevision=actual,baseSourceRevision=claimed,
           repositoryCIProvenanceClaimed=args.source_kind=="checkout",compilerVersions=versions,nativeExecuted=True,
           ordinaryUser=True,sourceFiles={name:sha(raw) for name,raw in source.items()},allSourceFilesUnchanged=True,
           temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,worksheetCompletionNotInferred=True,
           miriOnlyRejectedProgramNotExecutedNatively=True,foreignLibraryNotTested=True,allExecutionsNotProven=True,
           roles=roles,commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+"\n")
print(json.dumps({"accepted":True,"sourceKind":args.source_kind,"commands":len(commands),"consumerCases":272,"proof":str(args.proof)}))
