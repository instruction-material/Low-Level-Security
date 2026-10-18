"""Validate complete RSS7 source, bounded fixture acquisition and pure parser/CLI contracts."""
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
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "RUST-07-bounded-cli-evidence"
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


def run(command, cwd, label, expected=0, env=None):
    entry = dict(parentTaskId="rust-bounded-cli-evidence", parentPid=os.getpid(),
                 command=[os.fsdecode(value) for value in command], cwd=str(cwd),
                 startTime=datetime.datetime.now(datetime.UTC).isoformat(), timeoutSeconds=120)
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    entry["pid"] = child.pid
    with (OUT / "processes.jsonl").open("a") as stream:
        stream.write(json.dumps(dict(entry, event="start")) + "\n")
    stdout, stderr, cleanup = b"", b"", "owned process exited"
    try:
        stdout, stderr = child.communicate(timeout=120)
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
    commands.append(dict(label=label, exitCode=child.returncode,
                         stdoutSha256=sha(stdout), stderrSha256=sha(stderr)))
    return stdout, stderr


source_names = run(["git", "ls-files", "--", PACK.name, ".github/workflows/rust-bounded-cli.yml",
                    "test/verify_rust_bounded_cli.py"], ROOT, "source-inventory")[0].decode().splitlines()
assert len(source_names) == len(set(source_names)) == 23
source = {name: (ROOT / name).read_bytes() for name in source_names}
for name, raw in source.items():
    target = OUT / "source" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
versions = {}
for name, command in [("rustc", ["rustc", "-Vv"]), ("cargo", ["cargo", "-V"]),
                      ("rustfmt", ["rustfmt", "--version"]), ("clippy", ["cargo", "clippy", "--version"])]:
    versions[name] = run(command, ROOT, "version-" + name)[0].decode()
assert "release: 1.97.1\n" in versions["rustc"]
USAGE = b"usage: bounded_cli_lab --help | --file NAME.txt\n"


def predict(raw):
    def error(kind): return b"", ("error=input kind=" + kind + "\n").encode(), 65
    if len(raw) > 64: return error("too-large limit=64")
    try: text = raw.decode("utf-8")
    except UnicodeDecodeError: return error("invalid-utf8")
    rows = text.split("\n")
    if rows[-1] == "": rows.pop()
    labels, total = [], 0
    for line, record in enumerate(rows, 1):
        if line == 9: return error("too-many-rows limit=8")
        label, separator, number = record.partition("=")
        kind = None
        if not separator: kind = "missing-separator"
        elif not label or len(label.encode()) > 16 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-" for c in label): kind = "invalid-label"
        elif not number or any(c not in "0123456789" for c in number): kind = "invalid-number"
        elif int(number) > 65535: kind = "value-out-of-range"
        if kind: return b"", f"error=record line={line} kind={kind}\n".encode(), 65
        labels.append(label); total += int(number)
    return f"count={len(labels)} total={total} labels={'|'.join(labels) if labels else '-'}\n".encode(), b"", 0


corpus = []
for length in range(4):
    for rows in itertools.product(("a=0", "bad", "b=2"), repeat=length):
        raw = "\n".join(rows).encode()
        corpus.extend([raw, raw + b"\n"])
corpus += [b"abcdefghijklmnop=0", b"abcdefghijklmnopq=0", "café=2".encode(), b"a=", b"a=65535", b"a=65536", b"a=65536x", b"=no", b"a=+1", b"a=1\r\n", b"a=1=2", b"dash-=00017", b"a="+b"0"*61+b"1", b"a="+b"0"*61+b"10", b"\xff", b"bad\n\xff", b"\xff"*65, b"a=0\n"*8, b"a=0\n"*9, b"a=0\n"*8+b"bad", b"alpha=7\nprivate-invalid\nomega=17\n"]
assert len(corpus) == 101
usage = [[], ["--file"], ["--help", "extra"], ["--file", "valid.txt", "extra"], ["--file", "valid.txt", "extra", "more"], ["--unknown"], ["valid.txt"], ["--file", "../valid.txt"], ["--file", "/valid.txt"], ["--file", "a/b.txt"], ["--file", "a\\b.txt"], ["--file", ".txt"], ["--file", "a.b.txt"], ["--file", "a"*29+".txt"], ["--file", "c:valid.txt"]]
roles = []
with tempfile.TemporaryDirectory(prefix="rust-bounded-cli-") as temporary:
    work = Path(temporary)
    for role in ("starter", "solution"):
        selected = PACK / role
        project = work / role
        shutil.copytree(selected, project)
        lock = (project / "Cargo.lock").read_bytes()
        assert tomllib.loads((project/"Cargo.toml").read_text()) == {"package": {"name":"bounded_cli_lab", "version":"1.0.0", "edition":"2024"}}
        assert tomllib.loads(lock.decode())["package"] == [{"name":"bounded_cli_lab", "version":"1.0.0"}]
        env = {**os.environ, "CARGO_TARGET_DIR":str(work/(role+"-target")), "CARGO_NET_OFFLINE":"true"}
        run(["cargo", "fmt", "--all", "--check"], project, role+"-format", env=env)
        run(["cargo", "clippy", "--locked", "--offline", "--all-targets", "--", "-D", "warnings"], project, role+"-clippy", env=env)
        assert b"10 passed; 0 failed" in run(["cargo", "test", "--locked", "--offline"],project,role+"-tests",env=env)[0]
        run(["cargo", "build", "--locked", "--offline"],project,role+"-build",env=env)
        binary = Path(env["CARGO_TARGET_DIR"])/"debug/bounded_cli_lab"
        assert run([str(binary), "--help"],work,role+"-help",env=env)==(USAGE,b"")
        for name in ["valid", "empty", "malformed", "cap", "over"]:
            raw = (project/"fixtures"/(name+".txt")).read_bytes(); expected=predict(raw)
            assert run([str(binary),"--file",name+".txt"],work,role+"-fixture-"+name,expected=expected[2],env=env)==expected[:2]
        results=[]
        for index,raw in enumerate(corpus):
            (project/"fixtures/case.txt").write_bytes(raw)
            expected=predict(raw)
            assert run([str(binary),"--file","case.txt"],work,f"{role}-input-{index}",expected=expected[2],env=env)==expected[:2]
            results.append(dict(inputHex=raw.hex(),status=expected[2],stdoutSha256=sha(expected[0]),stderrSha256=sha(expected[1])))
        (project/"fixtures/case.txt").unlink()
        for index,arguments in enumerate(usage):
            assert run([str(binary),*arguments],work,f"{role}-usage-{index}",expected=64,env=env)==(b"",USAGE)
        for index,arguments in enumerate([[b"--file",b"\xff"],[b"\xff"]]):
            assert run([os.fsencode(binary),*arguments],work,f"{role}-invalid-utf8-{index}",expected=64,env=env)==(b"",USAGE)
        assert run([str(binary),"--file","missing.txt"],work,role+"-missing",expected=66,env=env)==(b"",b"error=read kind=not-found\n")
        folder=project/"fixtures/folder.txt";folder.mkdir()
        assert run([str(binary),"--file","folder.txt"],work,role+"-directory",expected=66,env=env)==(b"",b"error=read kind=not-regular\n")
        folder.rmdir()
        link=project/"fixtures/link.txt";link.symlink_to(project/"fixtures/valid.txt")
        assert run([str(binary),"--file","link.txt"],work,role+"-symlink",expected=66,env=env)==(b"",b"error=read kind=not-regular\n")
        link.unlink()
        run(["cargo","clean"],project,role+"-clean",env=env)
        assert not binary.exists()
        assert b"10 passed; 0 failed" in run(["cargo","test","--locked","--offline"],project,role+"-clean-tests",env=env)[0]
        run(["cargo","build","--locked","--offline"],project,role+"-clean-build",env=env)
        assert run([str(binary),"--file","valid.txt"],work,role+"-clean-valid",env=env)==predict(b"alpha=7\nbeta=17\n")[:2]
        assert (project/"Cargo.lock").read_bytes()==lock
        original={p.relative_to(selected):p.read_bytes() for p in selected.rglob("*") if p.is_file()}
        assert {p.relative_to(project):p.read_bytes() for p in project.rglob("*") if p.is_file()}==original
        saved=OUT/role;saved.mkdir();shutil.copyfile(binary,saved/"bounded_cli_lab")
        roles.append(dict(role=role,inputCases=len(corpus),unitTests=10,unitTestsBeforeAndAfterClean=True,sourceAndLockUnchanged=True,cases=results,executableSha256=sha(binary.read_bytes()),fixtureBoundaryChecks=3,usageRefusals=len(usage)+2,workingDirectoryIndependent=True))
assert not work.exists()
assert all((ROOT/name).read_bytes()==raw for name,raw in source.items())
assert len(commands)==5+2*(4+1+5+101+15+2+3+4)
proof=dict(sourceRevision=os.environ["SOURCE_REVISION"],compilerVersions=versions,nativeExecuted=True,ordinaryUser=True,sourceFiles={n:sha(r) for n,r in source.items()},allSourceFilesUnchanged=True,temporarySourceCleanup=True,externalDependencyDownloadsDuringChecks=False,worksheetCompletionNotInferred=True,byteBoundIsNotTimeBound=True,staticFixtureChecksAreNotRaceFreeConfinement=True,roles=roles,commands=commands)
args.proof.write_text(json.dumps(proof,indent=2)+"\n")
print(json.dumps(dict(sourceRevision=proof["sourceRevision"],sourceFiles=len(source),commands=len(commands),independentInputCases=2*len(corpus),unitResults=40)))
