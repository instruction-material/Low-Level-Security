"""Run the Cargo lesson's exact workflows against both unmodified source roles."""
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

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "RUST-00-cargo-tooling-evidence"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--proof", type=Path, required=True)
args = parser.parse_args()
args.proof = args.proof.resolve()
assert not args.proof.exists()
OUT = args.proof.parent
OUT.mkdir(parents=True, exist_ok=True)
assert os.getuid() != 0, "Use an ordinary account"


def cancel(signum, _frame):
    raise SystemExit(128 + signum)


signal.signal(signal.SIGINT, cancel)
signal.signal(signal.SIGTERM, cancel)


def now():
    return datetime.datetime.now(datetime.UTC).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


source = {str(path.relative_to(ROOT)): path.read_bytes()
          for path in PACK.rglob("*") if path.is_file()}
assert len(source) == 14
assert all(not (ROOT / name).is_symlink() for name in source)
for name in ("test/verify_rust_cargo_tooling.py", ".github/workflows/rust-cargo-tooling.yml"):
    source[name] = (ROOT / name).read_bytes()
for name, raw in source.items():
    target = OUT / "source" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
commands = []


def run(command, cwd, label, expected=0, env=None):
    entry = dict(parentTaskId="rust-cargo-tooling", parentPid=os.getpid(), command=[os.fsdecode(part) for part in command],
                 cwd=str(cwd), startTime=now(), timeoutSeconds=120)
    child = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, start_new_session=True)
    entry["pid"] = child.pid
    log = OUT / "processes.jsonl"
    with log.open("a") as stream:
        stream.write(json.dumps(dict(entry, event="start")) + "\n")
    stdout, stderr = b"", b""
    cleanup = "owned process exited"
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
        with log.open("a") as stream:
            stream.write(json.dumps(dict(entry, event="end", endTime=now(), exitCode=child.returncode,
                                         childProcessGroupCleanup=cleanup)) + "\n")
        (OUT / (label + ".stdout.txt")).write_bytes(stdout)
        (OUT / (label + ".stderr.txt")).write_bytes(stderr)
    commands.append(dict(label=label, exitCode=child.returncode, stdoutSha256=sha(stdout), stderrSha256=sha(stderr)))
    assert child.returncode == expected, (label, child.returncode, stderr.decode(errors="replace"))
    return stdout, stderr


versions = {}
for name, argv in [("rustc", ["rustc", "-Vv"]), ("cargo", ["cargo", "-V"]),
                   ("rustfmt", ["rustfmt", "--version"]), ("clippy", ["cargo", "clippy", "--version"])]:
    versions[name] = run(argv, ROOT, "version-" + name)[0].decode()
assert "release: 1.97.1\n" in versions["rustc"]
explicit = [("packet-42!", "packet-42"), ("A B_c/9", "ABc9"), ("", ""), ("---", "---"),
            ("café-42", "caf-42"), ("🦀", ""), ("../etc/passwd", "etcpasswd"),
            ("abcXYZ019-", "abcXYZ019-"), ("\talpha\nbeta\r", "alphabeta")]
alphabet = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
cases = list(explicit)
ascii_input = "".join(chr(code) for code in range(1, 128))
cases.append((ascii_input, "".join(character for character in ascii_input if character in alphabet)))
state = 0xC0A62024
for index in range(32):
    chars = []
    for _ in range(index):
        state = (state * 1664525 + 1013904223) % 2**32
        chars.append(chr(1 + state % 127))
    text = "".join(chars)
    cases.append((text, "".join(character for character in text if character in alphabet)))
roles = []
with tempfile.TemporaryDirectory(prefix="rust-cargo-tooling-") as temporary:
    work = Path(temporary)
    for role in ("starter", "solution"):
        selected = PACK / role
        directory = work / role
        shutil.copytree(selected, directory)
        env = {**os.environ, "CARGO_TARGET_DIR": str(work / (role + "-target")), "CARGO_TERM_COLOR": "never"}
        manifest = tomllib.loads((directory / "Cargo.toml").read_text())
        assert manifest["package"]["edition"] == "2024" and "dependencies" not in manifest
        lock = (directory / "Cargo.lock").read_bytes()
        assert tomllib.loads(lock.decode())["package"] == [{"name": "cargo_tooling_lab", "version": "0.1.0"}]
        run(["cargo", "fmt", "--all", "--check"], directory, role + "-format", env=env)
        run(["rustfmt", "--edition", "2024", "--check", "diagnostics/moved-value.rs", "diagnostics/fixed-value.rs"], directory, role + "-diagnostic-format", env=env)
        run(["cargo", "clippy", "--locked", "--offline", "--all-targets", "--", "-D", "warnings"], directory, role + "-clippy", env=env)
        test_output = run(["cargo", "test", "--locked", "--offline"], directory, role + "-tests", env=env)[0]
        assert b"3 passed; 0 failed" in test_output
        run(["cargo", "build", "--locked", "--offline"], directory, role + "-build", env=env)
        executable = Path(env["CARGO_TARGET_DIR"]) / "debug/cargo_tooling_lab"
        assert executable.is_file()
        program = directory / "src/main.rs"
        original = program.read_bytes()
        program.write_bytes(original.replace(b"use std::process::ExitCode;", b"use std :: process :: ExitCode;", 1))
        assert program.read_bytes() != original
        bad_format = run(["cargo", "fmt", "--all", "--check"], directory, role + "-format-refusal", expected=1, env=env)[0]
        assert bad_format
        run(["cargo", "fmt", "--all"], directory, role + "-format-repair", env=env)
        assert program.read_bytes() == original
        run(["cargo", "fmt", "--all", "--check"], directory, role + "-format-rechecked", env=env)
        run(["cargo", "clean"], directory, role + "-clean", env=env)
        assert not executable.exists()
        repeated = run(["cargo", "test", "--locked", "--offline"], directory, role + "-clean-tests", env=env)[0]
        assert b"3 passed; 0 failed" in repeated
        assert run(["cargo", "run", "--locked", "--offline"], directory, role + "-cargo-run-default", env=env)[0] == b"packet-42\n"
        assert run(["cargo", "run", "--locked", "--offline", "--", "A B_c/9"], directory, role + "-cargo-run-changed", env=env)[0] == b"ABc9\n"
        assert executable.is_file() and (directory / "Cargo.lock").read_bytes() == lock
        role_out = OUT / role
        role_out.mkdir()
        shutil.copyfile(executable, role_out / "cargo_tooling_lab")
        for index, (text, expected) in enumerate(cases):
            stdout, stderr = run([str(executable), text], directory, role + "-input-" + str(index), env=env)
            assert stdout == (expected + "\n").encode() and not stderr
        stdout, stderr = run([str(executable), "first", "second"], directory, role + "-invalid-arguments", expected=64, env=env)
        assert not stdout and stderr == b"usage: cargo_tooling_lab [label]\n"
        stdout, stderr = run([os.fsencode(executable), b"\xff"], directory, role + "-invalid-utf8", expected=64, env=env)
        assert not stdout and stderr == b"label must be valid UTF-8\n"
        failed_metadata = role_out / "moved.rmeta"
        stdout, stderr = run(["rustc", "--edition=2024", "--emit=metadata", "diagnostics/moved-value.rs", "-o", str(failed_metadata)], directory, role + "-moved-diagnostic", expected=1, env=env)
        assert not stdout and b"E0382" in stderr and not failed_metadata.exists()
        corrected = role_out / "fixed"
        run(["rustc", "--edition=2024", "diagnostics/fixed-value.rs", "-o", str(corrected)], directory, role + "-fixed-build", env=env)
        stdout, stderr = run([str(corrected)], directory, role + "-fixed-run", env=env)
        assert stdout == b"packet-42\npacket-42\n" and not stderr
        assert all((directory / name).read_bytes() == (selected / name).read_bytes()
                   for name in ("Cargo.toml", "Cargo.lock", "src/main.rs", "observations.md", "diagnostics/moved-value.rs", "diagnostics/fixed-value.rs"))
        roles.append(dict(role=role, formatRefusedAndRepaired=True, clippyWarningsDenied=True, unitTests=3,
                          unitSuitePassedBeforeAndAfterClean=True, cleanRemovedExecutable=True, cases=len(cases),
                          lockfileUnchanged=True, invalidArgumentExit=64, movedValueDiagnostic="E0382",
                          correctedProgramOutput="packet-42\npacket-42\n", executableSha256=sha(executable.read_bytes()),
                          correctedExecutableSha256=sha(corrected.read_bytes()), selectedSourceUnchanged=True))
assert not work.exists()
assert all((ROOT / name).read_bytes() == raw for name, raw in source.items())
proof = dict(sourceRevision=os.environ.get("SOURCE_REVISION"), compilerVersions=versions,
             sourceFiles={name: sha(raw) for name, raw in source.items()}, roles=roles, ordinaryUser=True,
             nativeExecuted=True, commands=commands, allSourceFilesUnchanged=True,
             externalDependencyDownloadsDuringChecks=False, temporarySourceCleanup=True)
args.proof.write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps(dict(roles=len(roles), independentInputCases=sum(role["cases"] for role in roles),
                     actualCommands=len(commands), temporarySourceCleanup=True)))
