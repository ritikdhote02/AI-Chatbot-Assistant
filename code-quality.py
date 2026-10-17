"""Format and validate the project's Python code."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "data",
    "dist",
    "env",
    "venv",
    ".venv",
    ".vscode",
    "vscode",
}


def find_python_files() -> list[Path]:
    """Return project Python files, excluding generated and local data folders."""
    python_files = []
    for current_directory, directories, filenames in os.walk(ROOT):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in EXCLUDED_DIRECTORIES
        )
        python_files.extend(
            Path(current_directory) / filename
            for filename in filenames
            if filename.endswith(".py")
        )
    return sorted(python_files)


def fix_whitespace(python_files: list[Path]) -> None:
    """Remove trailing spaces and ensure each non-empty file ends with a newline."""
    changed_files = 0

    for path in python_files:
        original = path.read_text(encoding="utf-8")
        lines = original.splitlines(keepends=True)
        cleaned_lines = []
        for line in lines:
            if line.endswith("\r\n"):
                body, ending = line[:-2], "\r\n"
            elif line.endswith(("\n", "\r")):
                body, ending = line[:-1], line[-1]
            else:
                body, ending = line, ""
            cleaned_lines.append(body.rstrip(" \t") + ending)

        cleaned = "".join(cleaned_lines)
        if cleaned:
            newline = "\r\n" if "\r\n" in original else "\n"
            cleaned = cleaned.rstrip("\r\n") + newline

        if cleaned != original:
            path.write_text(cleaned, encoding="utf-8", newline="")
            changed_files += 1

    print(f"Whitespace cleanup: updated {changed_files} file(s).")


def run_command(label: str, command: list[str]) -> bool:
    """Run one quality check and report its command and result."""
    print(f"\n--- {label} ---")
    print(f"$ {shlex.join(command)}")
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode == 0:
        print(f"PASS: {label}")
        return True

    print(f"FAIL: {label} (exit code {result.returncode})")
    return False


def main() -> int:
    python_files = find_python_files()
    if not python_files:
        print("No Python files found to check.")
        return 1

    relative_files = [str(path.relative_to(ROOT)) for path in python_files]
    all_passed = True

    all_passed &= run_command(
        "Sort imports",
        [sys.executable, "-m", "isort", *relative_files],
    )
    all_passed &= run_command(
        "Format code",
        [sys.executable, "-m", "black", *relative_files],
    )
    fix_whitespace(python_files)
    all_passed &= run_command(
        "Lint with Flake8",
        [sys.executable, "-m", "flake8", *relative_files],
    )
    all_passed &= run_command(
        "Check Python syntax",
        [sys.executable, "-m", "compileall", "-q", *relative_files],
    )

    if all_passed:
        print("\nCode quality checks passed.")
        return 0

    print(
        "\nOne or more code quality checks failed. "
        "Install the development tools with `poetry install --with dev` "
        "and fix any remaining Flake8 findings."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
