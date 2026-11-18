"""Run a trusted local script in a temporary directory with bounded output/time."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Thread


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str
    stderr: str
    stdout_truncated: bool = False
    stderr_truncated: bool = False


def _drain(stream, output: bytearray, limit: int, truncated: list[bool]) -> None:
    while chunk := stream.read(8192):
        remaining = limit - len(output)
        if remaining > 0:
            output.extend(chunk[:remaining])
        if len(chunk) > remaining:
            truncated[0] = True


def run_python_fixture(source: str, *, timeout_seconds: float = 2.0, output_limit: int = 4096) -> Result:
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout must be finite and positive")
    if isinstance(output_limit, bool) or not isinstance(output_limit, int) or output_limit < 1:
        raise ValueError("timeout and output limit must be positive")
    with tempfile.TemporaryDirectory(prefix="agent-lab-") as directory:
        root = Path(directory).resolve()
        script = root / "fixture.py"
        script.write_text(source, encoding="utf-8")
        process = subprocess.Popen(
            [sys.executable, "-I", str(script)], cwd=root, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=False,
        )
        stdout_bytes = bytearray()
        stderr_bytes = bytearray()
        stdout_truncated = [False]
        stderr_truncated = [False]
        readers = [
            Thread(target=_drain, args=(process.stdout, stdout_bytes, output_limit, stdout_truncated)),
            Thread(target=_drain, args=(process.stderr, stderr_bytes, output_limit, stderr_truncated)),
        ]
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait()
        finally:
            for reader in readers:
                reader.join()
        stdout = bytes(stdout_bytes).decode("utf-8", errors="replace")
        stderr = bytes(stderr_bytes).decode("utf-8", errors="replace")
        if timed_out:
            raise subprocess.TimeoutExpired(process.args, timeout_seconds, output=stdout, stderr=stderr)
        return Result(process.returncode, stdout, stderr, stdout_truncated[0], stderr_truncated[0])


def main() -> None:
    result = run_python_fixture("print('isolated fixture ok')")
    print(f"returncode={result.returncode} stdout={result.stdout.strip()}")


if __name__ == "__main__":
    main()
