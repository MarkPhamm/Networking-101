"""Interactive quiz verifier.

Curriculum items use `questions:` like so:

    questions:
      - id: dns_step
        prompt: "Which step is DNS resolution?"
        answer: "2"
        accept: ["2", "step 2", "dns"]   # optional extra accepted forms

When the student presses `v`, the verifier prompts each question in
turn on stdin. Answers are compared case-insensitively after stripping
whitespace and trailing punctuation. `answer` is always accepted;
`accept` adds extra synonyms.
"""

import os
import string
from pathlib import Path

import yaml
from rich.console import Console

from .base import BaseVerifier, TestResult, VerifyResult

_console = Console()

ROOT = Path(os.environ.get("NET_LEARN_ROOT", Path(__file__).parent.parent))
CURRICULUM_PATH = ROOT / "curriculum.yaml"


def _find_questions(item_path: str) -> list[dict] | None:
    resolved = Path(item_path).resolve()

    with open(CURRICULUM_PATH) as f:
        curriculum = yaml.safe_load(f)

    for stage in curriculum.get("stages", []):
        for item in stage.get("items", []):
            if not item.get("questions"):
                continue
            candidate = item.get("exercise") or item.get("lesson") or item.get("file")
            if not candidate:
                continue
            if (ROOT / candidate).resolve() == resolved:
                return item["questions"]

    return None


def _normalize(s: str) -> str:
    s = s.strip().lower()
    # drop trailing punctuation so "step 2." matches "step 2"
    return s.rstrip(string.punctuation + " ")


def _matches(user: str, answer: str, accept: list[str] | None) -> bool:
    candidates = [answer] + list(accept or [])
    target = _normalize(user)
    return any(_normalize(c) == target for c in candidates)


class QuizVerifier(BaseVerifier):
    """Prompt the student for each question on stdin and grade the replies."""

    def verify(self, exercise_path: str) -> VerifyResult:
        questions = _find_questions(exercise_path)
        if not questions:
            return VerifyResult(
                exercise_path=exercise_path,
                syntax_ok=True,
                syntax_error="No questions defined for this item in curriculum.yaml",
            )

        print()  # breathing room before the first prompt
        tests: list[TestResult] = []
        for i, q in enumerate(questions, 1):
            prompt = q.get("prompt", "")
            answer = str(q.get("answer", ""))
            accept = q.get("accept")
            qid = q.get("id", f"q{i}")

            print(f"Q{i}. {prompt}")
            try:
                user_answer = input("  > ")
            except (KeyboardInterrupt, EOFError):
                print()
                tests.append(TestResult(
                    name=qid, passed=False, message="skipped"
                ))
                continue

            if _matches(user_answer, answer, accept):
                _console.print("  [green]✔[/] correct\n")
                tests.append(TestResult(name=qid, passed=True))
            else:
                _console.print(f"  [red]✘[/] expected: [bold]{answer}[/]\n")
                tests.append(TestResult(
                    name=qid,
                    passed=False,
                    message=f"you answered {user_answer.strip()!r}; expected {answer!r}",
                ))

        return VerifyResult(
            exercise_path=exercise_path,
            syntax_ok=True,
            tests=tests,
        )
