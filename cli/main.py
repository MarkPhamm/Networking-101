#!/usr/bin/env python3
"""net-learn CLI — interactive Networking 101 learning environment."""

import subprocess
import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from cli.build import build_all, build_one, needs_rebuild, target_path
from cli.curriculum import CURRICULUM, CurriculumItem, get_index, get_item, reset_exercise
from cli.state import (
    is_done,
    is_verified,
    load_state,
    mark_done,
    mark_verified,
    save_state,
    unmark_verified,
)
from verifier.command import CommandVerifier
from verifier.file import FileVerifier
from verifier.local import LocalVerifier
from verifier.quiz import QuizVerifier


def _get_verifier(item: CurriculumItem):
    if item.verifier == "file":
        return FileVerifier()
    if item.verifier == "command":
        return CommandVerifier()
    if item.verifier == "quiz":
        return QuizVerifier()
    return LocalVerifier()


console = Console()
app = typer.Typer(
    name="net-learn",
    help="🌐 Networking 101 — interactive mode.",
    add_completion=False,
    no_args_is_help=False,
)


# --- Display ---

def show_item(item: CurriculumItem, state: dict) -> None:
    total = len(CURRICULUM)
    idx = get_index(item.id)
    done_count = len(state["done"])

    bar_width = 50
    filled = int(bar_width * done_count / total) if total > 0 else 0
    bar = "[green]" + "#" * filled + "[/]" + "-" * (bar_width - filled)

    type_label = "📖 Lesson" if item.type == "lesson" else "💪 Exercise"
    file_hint = ""
    if item.type == "exercise" and item.exercise_path:
        file_hint = (
            f"\n📁 File: [green]{item.exercise}[/]"
            f"\n[dim]Read the comments in the file for instructions.[/]"
        )
    elif item.type == "exercise" and item.verifier == "command":
        file_hint = "\n[dim]Run the commands from the lesson, then press [bold]v[/] to verify.[/]"
    elif item.type == "exercise" and item.verifier == "quiz":
        file_hint = "\n[dim]Knowledge check — press [bold]v[/] to answer the questions.[/]"

    console.print()
    console.print(Panel(
        f"[cyan][{idx + 1}/{total}][/] [bold]{item.title}[/]  {type_label}"
        f"{file_hint}",
        title=f"🌐 net-learn  ·  {item.stage_title}",
        border_style="bright_blue",
    ))
    console.print(f"Progress: [{bar}]  {done_count}/{total}")


def show_prompt(item: CurriculumItem) -> None:
    console.print("\n[dim]💡 Press [bold]l[/] to read the lesson before starting.[/]")
    parts = ["[bold]l[/]:lesson"]
    if item.has_verifier:
        parts.append("[bold]h[/]:hint")
        parts.append("[bold]v[/]:verify")
    parts.append("[bold]n[/]:next")
    parts.append("[bold]q[/]:quit")
    console.print("\n" + "  ".join(parts) + " ? ", end="")


# --- Actions ---

def action_read(item: CurriculumItem) -> None:
    path = item.lesson_path
    if not path or not path.exists():
        console.print("\n[dim]No lesson found for this item.[/]")
        return
    # Render markdown lessons to HTML on demand so Mermaid/tables/etc.
    # render nicely in the browser.
    if path.suffix.lower() == ".md":
        if needs_rebuild(path):
            build_one(path)
        path = target_path(path)
    console.print(f"\n[dim]Opening {path.name} in your browser...[/]")
    subprocess.Popen(["open", str(path)])


def action_verify(item: CurriculumItem, state: dict) -> bool:
    path = item.exercise_path or item.lesson_path
    if not path:
        console.print("\n[dim]No file to verify for this item.[/]")
        return False

    console.print(f"\n⏳ Verifying [cyan]{item.id}[/]...")
    result = _get_verifier(item).verify(str(path))

    if not result.syntax_ok:
        console.print(f"\n[red]✘ Syntax error[/] — {result.syntax_error}\n")
        return False

    if not result.tests:
        console.print("\n[red]✘ No tests were collected.[/]\n")
        return False

    for t in result.tests:
        icon = "[green]✔[/]" if t.passed else "[red]✘[/]"
        suffix = f" — {t.message}" if t.message else ""
        console.print(f"  {icon} {t.name}{suffix}")

    if result.extra:
        console.print(result.extra)

    if result.passed:
        mark_verified(state, item.id)
        save_state(state)
        console.print("\n[green]Exercise passed ✓[/]")
        console.print("When done experimenting, press [bold]n[/] to advance.\n")
    else:
        failed = len(result.failed_tests)
        total = len(result.tests)
        console.print(
            f"\n[red]❌ {failed}/{total} check(s) failed.[/] Fix and press [bold]v[/] to retry.\n"
        )

    return result.passed


def action_hint(item: CurriculumItem) -> None:
    hints = item.hints
    if not hints:
        console.print("\n[dim]No hints available for this exercise.[/]")
        return
    console.print(f"\n💡 [bold]Hints for {item.id}:[/]\n")
    for i, h in enumerate(hints, 1):
        console.print(f"[bold yellow]── Hint {i} ──[/]")
        console.print(Markdown(h))
        console.print()


def action_list(state: dict) -> None:
    console.print("\n🌐 [bold]net-learn — Curriculum[/]\n")
    current_stage = None
    for i, item in enumerate(CURRICULUM):
        if item.stage_id != current_stage:
            current_stage = item.stage_id
            console.print(f"  [bold]{item.stage_title}[/]")
        if is_done(state, item.id):
            status = "[green]✅[/]"
        elif item.id == state["current"]:
            status = "[yellow]▶ [/]"
        else:
            status = "  "
        type_tag = "[dim]lesson  [/]" if item.type == "lesson" else "[dim]exercise[/]"
        console.print(f"    {status} {i + 1:>2}. {type_tag}  {item.title}")
    console.print()


def action_next(item: CurriculumItem, state: dict) -> CurriculumItem | None:
    if item.has_verifier and not is_verified(state, item.id):
        console.print(
            "\n[yellow]⚠️  Finish the current exercise first.[/] "
            "Press [bold]v[/] to verify.\n"
        )
        return item

    state = mark_done(state, item.id)
    idx = get_index(item.id)

    if idx + 1 < len(CURRICULUM):
        next_item = CURRICULUM[idx + 1]
        state["current"] = next_item.id
        save_state(state)
        show_item(next_item, state)
        return next_item
    else:
        state["current"] = ""
        save_state(state)
        console.print("\n[green]🎉 You've completed the curriculum![/]\n")
        return None


# --- Interactive session ---

def interactive_session() -> None:
    state = load_state()
    save_state(state)
    item = get_item(state["current"]) if state["current"] else None

    if not item:
        console.print("[green]🎉 You've completed all exercises![/]")
        console.print("[dim]Run [bold]net-learn reset[/] to start over.[/]")
        return

    show_item(item, state)

    while item:
        show_prompt(item)
        try:
            cmd = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n👋 See you next time!")
            break

        if cmd == "q":
            console.print("\n👋 See you next time!")
            break
        elif cmd == "l":
            action_read(item)
        elif cmd == "v":
            if not item.has_verifier:
                console.print("\n[dim]No verifier for this item — press [bold]n[/] to advance.[/]")
            else:
                state = load_state()
                action_verify(item, state)
        elif cmd == "h":
            if not item.has_verifier:
                console.print("\n[dim]No hints for this item.[/]")
            else:
                action_hint(item)
        elif cmd == "n":
            state = load_state()
            result = action_next(item, state)
            if result is None:
                break
            item = result
        elif cmd == "x":
            if item.type == "lesson":
                console.print("\n[dim]Nothing to reset for a lesson.[/]")
            else:
                ok, msg = reset_exercise(item)
                if ok:
                    state = load_state()
                    unmark_verified(state, item.id)
                    save_state(state)
                icon = "[green]✔[/]" if ok else "[red]✘[/]"
                console.print(f"\n{icon} {msg}\n")
        else:
            console.print(f"\n[dim]Unknown command: '{cmd}'[/]")


# --- Typer commands ---

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """🌐 Networking 101 — interactive mode."""
    if ctx.invoked_subcommand is None:
        interactive_session()


@app.command(hidden=True)
def verify() -> None:
    """Verify the current exercise."""
    state = load_state()
    item = get_item(state["current"])
    if not item:
        console.print("[green]🎉 All done![/]")
        return
    if item.type == "lesson":
        console.print("[dim]Current item is a lesson. Use [bold]net-learn next[/] to advance.[/]")
        return
    action_verify(item, state)


@app.command(name="next", hidden=True)
def next_cmd() -> None:
    """Advance to the next item (exercises must pass first)."""
    state = load_state()
    item = get_item(state["current"])
    if not item:
        console.print("[green]🎉 All done![/]")
        return
    action_next(item, state)


@app.command(hidden=True)
def hint() -> None:
    """Show hints for the current exercise."""
    state = load_state()
    item = get_item(state["current"])
    if not item or item.type == "lesson":
        console.print("[dim]No hints available.[/]")
        return
    action_hint(item)


@app.command(name="list")
def list_cmd() -> None:
    """List all curriculum items and their status."""
    action_list(load_state())


@app.command()
def reset() -> None:
    """Reset all progress and restore exercise files to their originals."""
    console.print("[dim]Resetting progress...[/]")
    save_state({"current": CURRICULUM[0].id, "done": [], "verified": []})

    console.print("[dim]Restoring exercise files...[/]")
    for item in CURRICULUM:
        if item.type == "exercise" and item.original:
            reset_exercise(item)

    console.print("[green]✅ Reset complete. Run [bold]net-learn[/] to start over.[/]")


@app.command()
def build() -> None:
    """Render every lesson markdown to styled HTML in .lesson-cache/."""
    built = build_all()
    if not built:
        console.print("[dim]No markdown lessons to build.[/]")
        return
    for p in built:
        try:
            rel = p.relative_to(Path.cwd())
        except ValueError:
            rel = p
        console.print(f"[dim]→[/] {rel}")
    console.print(f"\n[green]✅ Generated {len(built)} HTML lesson(s).[/]")


@app.command(name="reset-exercise", hidden=True)
def reset_exercise_cmd() -> None:
    """Restore the current exercise to its original scaffold."""
    state = load_state()
    item = get_item(state["current"])
    if not item:
        console.print("[dim]No current exercise.[/]")
        return
    ok, msg = reset_exercise(item)
    icon = "[green]✔[/]" if ok else "[red]✘[/]"
    console.print(f"{icon} {msg}")


if __name__ == "__main__":
    app()
