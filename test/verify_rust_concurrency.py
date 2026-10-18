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
    entry = dict(parentTaskId="rust-concurrency-evidence", parentPid=os.getpid(),
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



claimed=os.environ["SOURCE_REVISION"]
assert len(claimed)==40 and all(c in "0123456789abcdef" for c in claimed)
expected_names=['.github/workflows/rust-concurrency.yml', 'RUST-08-concurrency-evidence/README.md', 'RUST-08-concurrency-evidence/solution/Cargo.lock', 'RUST-08-concurrency-evidence/solution/Cargo.toml', 'RUST-08-concurrency-evidence/solution/diagnostics/arc-owned.rs', 'RUST-08-concurrency-evidence/solution/diagnostics/cell-not-sync.rs', 'RUST-08-concurrency-evidence/solution/diagnostics/rc-not-send.rs', 'RUST-08-concurrency-evidence/solution/diagnostics/scoped-shared.rs', 'RUST-08-concurrency-evidence/solution/observations.md', 'RUST-08-concurrency-evidence/solution/src/ledger.rs', 'RUST-08-concurrency-evidence/solution/src/lib.rs', 'RUST-08-concurrency-evidence/solution/src/main.rs', 'RUST-08-concurrency-evidence/starter/Cargo.lock', 'RUST-08-concurrency-evidence/starter/Cargo.toml', 'RUST-08-concurrency-evidence/starter/diagnostics/arc-owned.rs', 'RUST-08-concurrency-evidence/starter/diagnostics/cell-not-sync.rs', 'RUST-08-concurrency-evidence/starter/diagnostics/rc-not-send.rs', 'RUST-08-concurrency-evidence/starter/diagnostics/scoped-shared.rs', 'RUST-08-concurrency-evidence/starter/observations.md', 'RUST-08-concurrency-evidence/starter/src/ledger.rs', 'RUST-08-concurrency-evidence/starter/src/lib.rs', 'RUST-08-concurrency-evidence/starter/src/main.rs', 'test/verify_rust_concurrency.py', 'test/verify_rust_concurrency_export.py']
actual_revision=None
if args.source_kind=="checkout":
    actual_revision=run(["git","rev-parse","HEAD"],ROOT,"actual-source-revision")[0].decode().strip()
    assert actual_revision==claimed,"Checked-out revision differs from claimed source"
    source_names=run(["git","ls-files","--",PACK.name,".github/workflows/rust-concurrency.yml","test/verify_rust_concurrency.py","test/verify_rust_concurrency_export.py"],ROOT,"source-inventory")[0].decode().splitlines()
    assert source_names==expected_names
else:
    source_names=expected_names
for name in source_names:
    cursor=ROOT
    for part in Path(name).parts:
        cursor=cursor/part
        assert not cursor.is_symlink(),"Linked source entry: "+name
    assert cursor.is_file(),"Missing source entry: "+name
package_files={name.removeprefix(PACK.name+"/") for name in expected_names if name.startswith(PACK.name+"/")}
package_dirs={Path(".")}
for name in package_files:package_dirs.update(Path(name).parents)
for relative in package_dirs:
    offset=0 if str(relative)=="." else len(relative.parts)
    children={Path(name).parts[offset] for name in package_files if Path(name).is_relative_to(relative) and len(Path(name).parts)>offset}
    assert {path.name for path in (PACK/relative).iterdir()}==children
source={name:(ROOT/name).read_bytes() for name in source_names}
assert all(b"\r" not in raw for raw in source.values())
committed_objects=verify_committed_bytes(actual_revision,source) if args.source_kind=="checkout" else None
versions = {name: run(command, ROOT, name)[0].decode().strip() for name, command in [
    ("rustc", ["rustc", "--version", "--verbose"]), ("cargo", ["cargo", "--version"]),
    ("rustfmt", ["rustfmt", "--version"]), ("clippy", ["cargo", "clippy", "--version"])]}
assert versions["rustc"].startswith("rustc 1.97.1 ")
USAGE = b"usage: concurrency_lab --help | --case NAME\n"
cases = {
    "valid": (b"count=2 total=24 ids=0|3\n", b"", 0),
    "empty": (b"count=0 total=0 ids=-\n", b"", 0),
    "cap": (b"count=8 total=524280 ids=0|1|2|3|4|5|6|7\n", b"", 0),
    **{name: (b"", ("error="+error+"\n").encode(), 65) for name, error in [
        ("fail", "worker-failed id=3"), ("cancel", "cancelled"), ("duplicate", "duplicate-id"),
        ("invalid-id", "invalid-id"), ("over", "too-many-items")]},
}
usage = [[], ["--case"], ["--help", "extra"], ["--case", "valid", "extra"],
         ["--case", "valid", "extra", "more"], ["--unknown"], ["valid"], ["--case", "unknown"]]

# This independent consumer supplies fixed vectors, without calling the CLI's case factory.
probe = r'''use concurrency_lab::{Job, Mode, run};
fn main() {
    for count in 0..=8 {
        for value in [0_u16, 1, 65535] {
            for reverse in [false, true] {
                let mut jobs: Vec<_> = (0..count).map(|id| Job { id, value }).collect();
                if reverse { jobs.reverse(); }
                let result = run(jobs, Mode::Normal);
                let life = &result.lifecycle;
                let report = result.report.unwrap();
                println!("normal {count} {value} {reverse} {} {} {} {} {} {}", report.total,
                         report.ids.iter().map(usize::to_string).collect::<Vec<_>>().join("|"),
                         life.spawned, life.joined, life.received, life.channel_closed);
            }
        }
    }
    let result = run(vec![Job { id: 7, value: 0 }, Job { id: 2, value: 65535 }, Job { id: 4, value: 0 }], Mode::Normal);
    let life = &result.lifecycle;
    let report = result.report.unwrap();
    println!("sparse {} {} {} {} {} {}", report.total,
             report.ids.iter().map(usize::to_string).collect::<Vec<_>>().join("|"),
             life.spawned, life.joined, life.received, life.channel_closed);
    for id in 0..8 {
        let jobs = (0..8).map(|id| Job { id, value: 7 }).collect();
        let result = run(jobs, Mode::FailItem(id));
        assert_eq!(result.report, Err(concurrency_lab::RunError::WorkerFailed(id)));
        assert!(result.lifecycle.cancelled);
        println!("failed {id} {} {} {}", result.lifecycle.spawned, result.lifecycle.joined, result.lifecycle.channel_closed);
    }
    let result = run(vec![Job { id: 7, value: 7 }], Mode::CancelBeforeStart);
    assert_eq!(result.report, Err(concurrency_lab::RunError::Cancelled));
    assert!(result.lifecycle.cancelled);
    assert_eq!(result.lifecycle.received, 0);
    println!("cancelled {} {} {}", result.lifecycle.spawned, result.lifecycle.joined, result.lifecycle.channel_closed);
}
'''
roles = []
with tempfile.TemporaryDirectory(prefix="rust-concurrency-") as temporary:
    work = Path(temporary)
    for role in ("starter", "solution"):
        selected = PACK / role
        project = work / role
        shutil.copytree(selected, project)
        original = {p.relative_to(selected): p.read_bytes() for p in selected.rglob("*") if p.is_file()}
        lock = (project / "Cargo.lock").read_bytes()
        assert tomllib.loads((project/"Cargo.toml").read_text()) == {"package": {"name":"concurrency_lab", "version":"1.0.0", "edition":"2024"}}
        assert tomllib.loads(lock.decode())["package"] == [{"name":"concurrency_lab", "version":"1.0.0"}]
        env = {**os.environ, "CARGO_TARGET_DIR":str(work/(role+"-target")), "CARGO_NET_OFFLINE":"true"}
        run(["cargo", "fmt", "--all", "--check"], project, role+"-format", env=env)
        diagnostics = sorted((project/"diagnostics").glob("*.rs"))
        assert len(diagnostics) == 4
        run(["rustfmt", "--edition", "2024", "--check", *map(str, diagnostics)], project, role+"-diagnostic-format", env=env)
        run(["cargo", "clippy", "--locked", "--offline", "--all-targets", "--", "-D", "warnings"], project, role+"-clippy", env=env)
        assert b"17 passed; 0 failed" in run(["cargo", "test", "--locked", "--offline"],project,role+"-tests",env=env)[0]
        run(["cargo", "build", "--locked", "--offline"],project,role+"-build",env=env)
        binary = Path(env["CARGO_TARGET_DIR"])/"debug/concurrency_lab"
        assert run([str(binary), "--help"],work,role+"-help",env=env,timeout=30)==(USAGE,b"")
        for repeat in range(3):
            for name, expected in cases.items():
                assert run([str(binary),"--case",name],work,f"{role}-case-{name}-{repeat}",expected=expected[2],env=env,timeout=30)==expected[:2]
        for index, arguments in enumerate(usage):
            assert run([str(binary), *arguments],work,f"{role}-usage-{index}",expected=64,env=env,timeout=30)==(b"",USAGE)
        for index, arguments in enumerate([[b"--case", b"\xff"],[b"\xff"]]):
            assert run([os.fsencode(binary), *arguments],work,f"{role}-utf8-{index}",expected=64,env=env,timeout=30)==(b"",USAGE)
        for diagnostic in diagnostics:
            rejected = diagnostic.stem in {"rc-not-send", "cell-not-sync"}
            target = work / (role+"-"+diagnostic.stem)
            out, err = run(["rustc","--edition=2024","--error-format=json",str(diagnostic),"-o",str(target)],work,role+"-"+diagnostic.stem+"-compile",expected=int(rejected),env=env)
            assert out == b""
            if rejected:
                messages=[json.loads(line) for line in err.splitlines()]
                assert any(message.get("code",{}).get("code")=="E0277" for message in messages if isinstance(message.get("code"),dict))
                assert not target.exists()
            else:
                assert err == b""
                assert run([str(target)],work,role+"-"+diagnostic.stem+"-run",env=env,timeout=30)==(b"7\n",b"")
        harness = work / (role+"-consumer.rs")
        harness.write_text(probe)
        consumer = work / (role+"-consumer")
        run(["rustc", "--edition=2024", "--crate-name", "consumer", str(harness), "--extern",
             "concurrency_lab="+str(Path(env["CARGO_TARGET_DIR"])/"debug/libconcurrency_lab.rlib"),
             "-L", "dependency="+str(Path(env["CARGO_TARGET_DIR"])/"debug/deps"), "-o", str(consumer)],work,role+"-consumer-compile",env=env)
        output, err = run([str(consumer)],work,role+"-consumer-run",env=env,timeout=30)
        assert err == b""
        rows = output.decode().splitlines()
        assert len(rows) == 64
        for index, row in enumerate(rows[:54]):
            # Empty IDs form a blank field, preserved by split(" ").
            kind,count,value,reverse,total,ids,spawned,joined,received,closed = row.split(" ")
            count,value,total,spawned,joined,received = map(int,[count,value,total,spawned,joined,received])
            assert kind == "normal" and reverse in {"true","false"}
            assert count == index//6 and value == [0,1,65535][index//2%3]
            assert total == count*value and ids == "|".join(map(str,range(count)))
            assert received == count and spawned == joined == (2 if role=="solution" else 0)
            assert closed == str(role=="solution").lower()
        assert rows[54].split() == ["sparse", "65535", "2|4|7", "2" if role=="solution" else "0", "2" if role=="solution" else "0", "3", str(role=="solution").lower()]
        for index, row in enumerate(rows[55:63]):
            kind, id_value, spawned, joined, closed = row.split()
            assert kind == "failed" and int(id_value) == index
            assert spawned == joined == ("2" if role=="solution" else "0")
            assert closed == str(role=="solution").lower()
        kind,spawned,joined,closed = rows[63].split()
        assert kind == "cancelled" and spawned == joined == ("2" if role=="solution" else "0")
        assert closed == str(role=="solution").lower()
        run(["cargo","clean"],project,role+"-clean",env=env)
        assert not binary.exists()
        assert b"17 passed; 0 failed" in run(["cargo","test","--locked","--offline"],project,role+"-clean-tests",env=env)[0]
        run(["cargo","build","--locked","--offline"],project,role+"-clean-build",env=env)
        assert run([str(binary),"--case","valid"],work,role+"-clean-valid",env=env,timeout=30)==cases["valid"][:2]
        assert {p.relative_to(project):p.read_bytes() for p in project.rglob("*") if p.is_file()}==original
        saved=OUT/role
        saved.mkdir()
        shutil.copyfile(binary,saved/"concurrency_lab")
        roles.append(dict(role=role,unitTests=17,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,
                          nativeContractCases=64,cliCases=24,usageRefusals=10,compilerRefusals=2,
                          executableSha256=sha(binary.read_bytes()),lifecycleProbeRows=rows,
                          observedProbeElapsedSeconds=next(c["elapsedSeconds"] for c in commands if c["label"]==role+"-consumer-run")))
assert not work.exists() and all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==(111 if args.source_kind=="checkout" else 108)
proof=dict(sourceKind=args.source_kind,sourceDiscovery="git-index" if args.source_kind=="checkout" else "fixed-filesystem",
           baseSourceRevision=claimed,repositoryCIProvenanceClaimed=args.source_kind=="checkout",committedSourceObjects=committed_objects,sourceRevision=actual_revision,checkedOutRevision=actual_revision,compilerVersions=versions,nativeExecuted=True,
           ordinaryUser=True,sourceFiles={n:sha(r) for n,r in source.items()},allSourceFilesUnchanged=True,
           temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,
           receiveDeadlineNotWholeProcessGuarantee=True,allSchedulesNotProven=True,
           injectedWorkerErrorNotArbitraryPanicOrHostSpawnFailure=True,
           worksheetCompletionNotInferred=True,roles=roles,commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+"\n")
print(json.dumps({"accepted":True,"roles":len(roles),"nativeContractCases":128,"commands":len(commands),"proof":str(args.proof)}))
