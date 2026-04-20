"""Verify exercises by running shell commands and checking their output.

Curriculum items use `command_checks:` with entries like:

    command_checks:
      - name: "ssh key exists"
        command: "test -f ~/.ssh/id_ed25519_learn"
        expect_returncode: 0

      - name: "dig resolves example.com"
        command: "dig +short example.com"
        expect_stdout_regex: "^\\d+\\.\\d+\\.\\d+\\.\\d+$"

Each entry runs via the shell. A check passes when all specified
expectations match (returncode, stdout regex, stderr regex).
"""

import os
import re
import subprocess
from pathlib import Path

import yaml

from .base import BaseVerifier, TestResult, VerifyResult

ROOT = Path(os.environ.get("NET_LEARN_ROOT", Path(__file__).parent.parent))
CURRICULUM_PATH = ROOT / "curriculum.yaml"
DEFAULT_TIMEOUT = 30


def _find_command_checks(item_path: str) -> list[dict] | None:
    resolved = Path(item_path).resolve()

    with open(CURRICULUM_PATH) as f:
        curriculum = yaml.safe_load(f)

    for stage in curriculum.get("stages", []):
        for item in stage.get("items", []):
            candidate = item.get("exercise") or item.get("lesson") or item.get("file")
            if not candidate:
                continue
            if (ROOT / candidate).resolve() == resolved:
                return item.get("command_checks")

    return None


def _run_one(check: dict) -> TestResult:
    name = check.get("name", check["command"])
    command = check["command"]
    timeout = check.get("timeout", DEFAULT_TIMEOUT)

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            name=name,
            passed=False,
            message=f"timed out after {timeout}s",
        )

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    failures: list[str] = []

    if "expect_returncode" in check and proc.returncode != check["expect_returncode"]:
        failures.append(
            f"returncode={proc.returncode} (expected {check['expect_returncode']})"
        )

    if "expect_stdout_regex" in check and not re.search(
        check["expect_stdout_regex"], stdout, re.MULTILINE
    ):
        snippet = (stdout[:120] + "…") if len(stdout) > 120 else stdout
        failures.append(f"stdout did not match /{check['expect_stdout_regex']}/ — got: {snippet!r}")

    if "expect_stdout_contains" in check and check["expect_stdout_contains"] not in stdout:
        failures.append(
            f"stdout did not contain {check['expect_stdout_contains']!r}"
        )

    if "expect_stderr_regex" in check and not re.search(
        check["expect_stderr_regex"], stderr, re.MULTILINE
    ):
        failures.append(f"stderr did not match /{check['expect_stderr_regex']}/")

    if failures:
        return TestResult(name=name, passed=False, message="; ".join(failures))
    return TestResult(name=name, passed=True)


class CommandVerifier(BaseVerifier):
    """Run each entry in `command_checks:` and aggregate results."""

    def verify(self, exercise_path: str) -> VerifyResult:
        checks = _find_command_checks(exercise_path)
        if not checks:
            return VerifyResult(
                exercise_path=exercise_path,
                syntax_ok=True,
                syntax_error="No command_checks defined for this exercise in curriculum.yaml",
            )

        tests = [_run_one(c) for c in checks]
        return VerifyResult(
            exercise_path=exercise_path,
            syntax_ok=True,
            tests=tests,
        )
