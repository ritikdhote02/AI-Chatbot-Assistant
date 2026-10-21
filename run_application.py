"""Install dependencies and run the backend and frontend together."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"


def stop_process(process: subprocess.Popen) -> None:
    """Stop a server process, including its child processes where supported."""
    if process.poll() is not None:
        return

    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=10)
    except ProcessLookupError:
        pass
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()


def install_dependencies(poetry: str, npm: str) -> bool:
    commands = [
        ("backend dependencies", [poetry, "install", "--with", "dev"], ROOT),
        ("frontend dependencies", [npm, "ci"], FRONTEND),
    ]

    for label, command, directory in commands:
        print(f"\nInstalling {label}...", flush=True)
        result = subprocess.run(command, cwd=directory, check=False)
        if result.returncode != 0:
            print(
                f"Failed to install {label} (exit code {result.returncode}).",
                file=sys.stderr,
            )
            return False

    return True


def main() -> int:
    poetry = shutil.which("poetry")
    npm = shutil.which("npm")
    if poetry is None or npm is None:
        missing = []
        if poetry is None:
            missing.append("Poetry")
        if npm is None:
            missing.append("npm")
        print(
            "Required command(s) not found on PATH: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    if not (FRONTEND / "package.json").is_file():
        print(f"Frontend package.json not found at {FRONTEND}.", file=sys.stderr)
        return 1

    try:
        if not install_dependencies(poetry, npm):
            return 1

        print("\nStarting backend and frontend. Press Ctrl+C to stop both.", flush=True)
        processes = []
        try:
            backend = subprocess.Popen(
                [poetry, "run", "uvicorn", "app.main:app", "--reload"],
                cwd=ROOT,
                start_new_session=(os.name == "posix"),
            )
            processes.append(("Backend", backend))

            frontend = subprocess.Popen(
                [npm, "run", "dev"],
                cwd=FRONTEND,
                start_new_session=(os.name == "posix"),
            )
            processes.append(("Frontend", frontend))

            print("Backend:  http://127.0.0.1:8000/docs", flush=True)
            print("Frontend: http://localhost:5173", flush=True)

            while True:
                for label, process in processes:
                    return_code = process.poll()
                    if return_code is not None:
                        print(
                            f"\n{label} stopped (exit code {return_code}); "
                            "stopping the other server.",
                            flush=True,
                        )
                        return return_code
                time.sleep(0.5)
        finally:
            for _, process in processes:
                stop_process(process)
    except KeyboardInterrupt:
        print("\nStopping application...", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
