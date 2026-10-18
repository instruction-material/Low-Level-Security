"""Validate complete RSS6 source, observable iterator work and actual library contracts."""
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
PACK = ROOT / "RUST-06-trait-pipeline-evidence"
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
    entry = dict(parentTaskId="rust-trait-pipeline-evidence", parentPid=os.getpid(),
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


source_names = run(["git", "ls-files", "--", PACK.name, ".github/workflows/rust-trait-pipeline.yml",
                    "test/verify_rust_trait_pipeline.py"], ROOT, "source-inventory")[0].decode().splitlines()
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
USAGE = b"usage: trait_pipeline_lab [--audit | --all] [row ...; at most 16]\n"


def parse(text):
    if "=" not in text:
        return None, "missing-separator"
    label, number = text.split("=", 1)
    if not 1 <= len(label) <= 16 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-" for c in label):
        return None, "invalid-label"
    if not number or any(c not in "0123456789" for c in number):
        return None, "invalid-number"
    value = int(number)
    if value > 65535:
        return None, "value-out-of-range"
    return (label, value), None


def predict(role, mode, rows):
    if mode == "--all":
        lines, failed = [], False
        for index, text in enumerate(rows, 1):
            value, error = parse(text)
            if error:
                lines.append(f"row={index} error={error}\n")
                failed = True
            else:
                lines.append(f"row={index} label={value[0]} value={value[1]}\n")
        return ("".join(lines) + f"pulls={len(rows)}\n").encode(), b"", 65 if failed else 0
    labels, total = [], 0
    for index, text in enumerate(rows, 1):
        value, error = parse(text)
        if error:
            pulls = len(rows) if role == "starter" else index
            return f"pulls={pulls}\n".encode(), f"row={index} error={error}\n".encode(), 65
        labels.append(value[0])
        total += value[1]
    return f"count={len(rows)} total={total} labels={'|'.join(labels) if labels else '-'}\npulls={len(rows)}\n".encode(), b"", 0


row_sets = [list(rows) for size in range(4) for rows in itertools.product(["alpha=7", "bad", "beta=0"], repeat=size)]
boundaries = ["abcdefghijklmnop=0", "abcdefghijklmnopq=0", "café=2", "a=", "a=65535", "a=65536",
              "a=65536x", "=no", "a=+1", "a=1\n", "dash-=00017", "a=" + "0" * 50 + "17"]
row_sets += [[row] for row in boundaries]
row_sets += [["alpha=65535"] * 16, ["bad", *(["beta=0"] * 15)]]
assert len(row_sets) == 54
cases = [(mode, rows) for mode in ("--audit", "--all") for rows in row_sets]
assert len(cases) == 108
roles = []
with tempfile.TemporaryDirectory(prefix="rust-trait-pipeline-") as temporary:
    work = Path(temporary)
    for role in ("starter", "solution"):
        selected = PACK / role
        project = work / role
        shutil.copytree(selected, project)
        lock = (project / "Cargo.lock").read_bytes()
        manifest = tomllib.loads((project / "Cargo.toml").read_text())
        assert manifest == {"package": {"name": "trait_pipeline_lab", "version": "1.0.0", "edition": "2024"}}
        assert tomllib.loads(lock.decode())["package"] == [{"name": "trait_pipeline_lab", "version": "1.0.0"}]
        env = {**os.environ, "CARGO_TARGET_DIR": str(work / (role + "-target")), "CARGO_NET_OFFLINE": "true"}
        run(["cargo", "fmt", "--all", "--check"], project, role + "-format", env=env)
        diagnostic_files = sorted(str(path.relative_to(project)) for path in (project / "diagnostics").glob("*.rs"))
        assert len(diagnostic_files) == 5
        run(["rustfmt", "--edition", "2024", "--check", *diagnostic_files], project, role + "-diagnostic-format", env=env)
        run(["cargo", "clippy", "--locked", "--offline", "--all-targets", "--", "-D", "warnings"], project, role + "-clippy", env=env)
        assert b"8 passed; 0 failed" in run(["cargo", "test", "--locked", "--offline"], project, role + "-tests", env=env)[0]
        run(["cargo", "build", "--locked", "--offline"], project, role + "-build", env=env)
        binary = Path(env["CARGO_TARGET_DIR"]) / "debug/trait_pipeline_lab"
        default = predict(role, "--audit", ["alpha=7", "beta=17"])
        assert run([str(binary)], project, role + "-default", env=env) == default[:2]
        results = []
        for index, (mode, rows) in enumerate(cases):
            expected = predict(role, mode, rows)
            assert run([str(binary), mode, *rows], project, f"{role}-input-{index}", expected=expected[2], env=env) == expected[:2]
            results.append(dict(mode=mode, rows=rows, status=expected[2], stdoutSha256=sha(expected[0]), stderrSha256=sha(expected[1])))
        for index, arguments in enumerate([["unknown"], ["alpha=7"], ["--audit", *(["a=0"] * 17)], ["--all", *(["a=0"] * 17)]]):
            assert run([str(binary), *arguments], project, f"{role}-usage-{index}", expected=64, env=env) == (b"", USAGE)
        for index, arguments in enumerate([[b"--audit", b"\xff"], [b"\xff"]]):
            assert run([os.fsencode(binary), *arguments], project, f"{role}-invalid-utf8-{index}", expected=64, env=env) == (b"", USAGE)
        saved = OUT / role
        saved.mkdir()
        diagnostic_hashes = {}
        for name in ("alternate-source", "missing-method", "mutate-live-iterator", "mutation-after-last-use", "report-after-owner-drop"):
            code = {"missing-method": "E0046", "mutate-live-iterator": "E0502"}.get(name)
            if name == "alternate-source" and role == "starter":
                code = "E0308"
            if name == "report-after-owner-drop" and role == "solution":
                code = "E0505"
            target = saved / name
            command = ["rustc", "--edition=2024", "--extern", "trait_pipeline_lab=" + str(Path(env["CARGO_TARGET_DIR"]) / "debug/libtrait_pipeline_lab.rlib"),
                       "-L", "dependency=" + str(Path(env["CARGO_TARGET_DIR"]) / "debug/deps"), "diagnostics/" + name + ".rs", "-o", str(target)]
            stdout, stderr = run(command, project, role + "-" + name + "-build", expected=1 if code else 0, env=env)
            if code:
                assert not stdout and code.encode() in stderr and not target.exists()
            else:
                output = {"alternate-source": b"count=2 total=12\n", "mutation-after-last-use": b"rows=2\n", "report-after-owner-drop": b"alpha\n"}[name]
                assert run([str(target)], project, role + "-" + name + "-run", env=env) == (output, b"")
                diagnostic_hashes[name] = sha(target.read_bytes())
        run(["cargo", "clean"], project, role + "-clean", env=env)
        assert not binary.exists()
        assert b"8 passed; 0 failed" in run(["cargo", "test", "--locked", "--offline"], project, role + "-clean-tests", env=env)[0]
        run(["cargo", "build", "--locked", "--offline"], project, role + "-clean-build", env=env)
        assert run([str(binary)], project, role + "-clean-default", env=env) == default[:2]
        assert (project / "Cargo.lock").read_bytes() == lock
        assert all(path.read_bytes() == (selected / path.relative_to(project)).read_bytes() for path in project.rglob("*") if path.is_file())
        shutil.copyfile(binary, saved / "trait_pipeline_lab")
        roles.append(dict(role=role, inputCases=108, unitTests=8, unitTestsBeforeAndAfterClean=True,
                          sourceAndLockUnchanged=True, cases=results, executableSha256=sha(binary.read_bytes()),
                          diagnosticExecutableSha256=diagnostic_hashes,
                          consumer="concrete eager owned baseline" if role == "starter" else "generic lazy borrowed target"))
assert not work.exists() and all((ROOT / name).read_bytes() == raw for name, raw in source.items())
assert len(commands) == 267, len(commands)
proof = dict(sourceRevision=os.environ.get("SOURCE_REVISION"), sourceFiles={name: sha(raw) for name, raw in source.items()},
             compilerVersions=versions, commands=commands, roles=roles, nativeExecuted=True, ordinaryUser=True,
             allSourceFilesUnchanged=True, temporarySourceCleanup=True, externalDependencyDownloadsDuringChecks=False,
             worksheetCompletionNotInferred=True, arbitrarySourceFinitenessNotClaimed=True, productionResourcePolicyNotClaimed=True)
args.proof.write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps(dict(sourceFiles=23, commands=len(commands), inputCases=216, compilerRefusals=6, nativeExecutables=6)))
