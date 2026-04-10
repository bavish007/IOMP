from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import textwrap
<<<<<<< HEAD
import time
=======
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07
import webbrowser
from dataclasses import dataclass

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
<<<<<<< HEAD
from rich.live import Live
=======
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07

from .core.models import ShellType, dataclass_to_dict
from .core.service import CommandService


console = Console()

<<<<<<< HEAD
HEADER = "J.A.R.V.I.S. Kernel"
SEPARATOR = "=" * 72

def animated_print(text: str, delay: float = 0.01) -> None:
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()

=======
HEADER = "Talk2Shell Launcher"
SEPARATOR = "=" * 72

>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07

@dataclass(slots=True)
class SessionConfig:
    shell: ShellType = ShellType.bash if os.name != "nt" else ShellType.powershell
    dry_run: bool = False
<<<<<<< HEAD
    confirm_risky: bool = True
    mode: str = "autonomous"
=======
    confirm_risky: bool = False
    mode: str = "standard"
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07


@dataclass(slots=True)
class SessionRecord:
    instruction: str
    status: str
    summary: str
    shell: str


def _is_windows() -> bool:
    return os.name == "nt"


def _is_admin() -> bool:
    if not _is_windows():
        return hasattr(os, "geteuid") and os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _run_in_native_terminal(script_args: list[str]) -> bool:
    if not _is_windows():
        console.print("[yellow]Native Windows terminal launch is only available on Windows.[/yellow]")
        return False

    python_executable = sys.executable
    script_path = os.path.abspath(sys.argv[0])

    wt_path = shutil.which("wt.exe") or shutil.which("wt")
    if wt_path:
        launch_command = [python_executable, script_path, *script_args]
        subprocess.Popen([wt_path, "new-tab", "cmd", "/k", *launch_command], close_fds=True)
        return True

    powershell_path = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
    if powershell_path:
        command_text = f'Start-Process -WindowStyle Normal -FilePath "{python_executable}" -ArgumentList "{script_path} {' '.join(script_args)}"'
        subprocess.Popen([powershell_path, "-NoProfile", "-Command", command_text], close_fds=True)
        return True

    cmd_path = shutil.which("cmd.exe") or shutil.which("cmd")
    if cmd_path:
        command_text = f'start "Talk2Shell" "{python_executable}" "{script_path}" {' '.join(script_args)}'
        subprocess.Popen([cmd_path, "/c", command_text], close_fds=True)
        return True

    console.print("[red]No native Windows terminal launcher was found.[/red]")
    return False


def _relaunch_as_admin() -> bool:
    if not _is_windows():
        console.print("[yellow]Administrator mode is only available on Windows.[/yellow]")
        return False

    if _is_admin():
        console.print("[green]Already running with administrator privileges.[/green]")
        return True

    executable = sys.executable
    script = os.path.abspath(sys.argv[0])
    params = f'"{script}" --launcher --terminal'
    try:
        result = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        if result <= 32:
            console.print("[red]Failed to request elevation.[/red]")
            return False
        console.print("[green]Administrator prompt opened. Relaunching...[/green]")
        return True
    except Exception as error:
        console.print(f"[red]Unable to relaunch as administrator: {error}[/red]")
        return False


def _print_block(title: str, content: str, color_code: str = "36") -> None:
    console.print(f"\033[{color_code}m{title}\033[0m")
    console.print(content)
    console.print()


def _print_result(label: str, payload: dict[str, object], color_code: str = "36") -> None:
    pretty = json.dumps(payload, indent=2)
    _print_block(label, pretty, color_code)


def _render_banner() -> None:
<<<<<<< HEAD
    jarvis_logo = [
        r"       _     _      ____   __     __  ___   ____  ",
        r"      | |   / \    |  _ \  \ \   / / |_ _| / ___| ",
        r"   _  | |  / _ \   | |_) |  \ \ / /   | |  \___ \ ",
        r"  | |_| | / ___ \  |  _ <    \ V /    | |   ___) |",
        r"   \___/ /_/   \_\ |_| \_\    \_/    |___| |____/ "
    ]
    
    current_logo = ""
    with Live(refresh_per_second=20, transient=False) as live:
        for line in jarvis_logo:
            current_logo += line + "\n"
            banner = Panel.fit(
                f"[bold bright_blue]{current_logo}[/bold bright_blue][cyan]J.A.R.V.I.S. Core Systems Online[/cyan]",
                box=box.ROUNDED,
                border_style="bright_blue",
            )
            live.update(banner)
            time.sleep(0.15)


def _render_mode_table(config: SessionConfig) -> None:
    pass


def _render_quick_help() -> None:
    pass


def _render_status_strip(config: SessionConfig, records: list[SessionRecord]) -> None:
    pass
=======
    banner = Panel.fit(
        "[bold cyan]Talk2Shell[/bold cyan]\n[white]Terminal-first launcher with offline and online modes[/white]",
        box=box.DOUBLE,
        border_style="cyan",
    )
    console.print(banner)


def _render_mode_table(config: SessionConfig) -> None:
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right", style="cyan")
    table.add_column(style="white")
    table.add_row("Shell", config.shell.value)
    table.add_row("Dry run", "on" if config.dry_run else "off")
    table.add_row("Confirm risky", "on" if config.confirm_risky else "off")
    table.add_row("Mode", config.mode)
    console.print(table)


def _render_quick_help() -> None:
    console.print(
        Panel(
            "[bold]Quick controls[/bold]\n"
            "• Enter natural language to run a command\n"
            "• :shell powershell|bash\n"
            "• :dryrun on|off\n"
            "• :confirm on|off\n"
            "• :details on|off\n"
            "• :history\n"
            "• :back / :quit",
            border_style="bright_blue",
            title="Controls",
        )
    )


def _render_status_strip(config: SessionConfig, records: list[SessionRecord]) -> None:
    status_card = Panel(
        f"[bold]Mode[/bold] {config.mode}\n[bold]Shell[/bold] {config.shell.value}\n[bold]Execution[/bold] {'live' if not config.dry_run else 'dry-run'}",
        border_style="cyan",
        title="Session",
    )
    safety_card = Panel(
        f"[bold]Risk confirmation[/bold] {'on' if config.confirm_risky else 'off'}\n[bold]Recent commands[/bold] {len(records)}",
        border_style="yellow",
        title="Status",
    )
    instructions_card = Panel(
        "Type a natural-language command and press Enter.\nUse `:help` for controls, `:history` for the last results.",
        border_style="bright_black",
        title="Usage",
    )
    console.print(Columns([status_card, safety_card, instructions_card], expand=True))
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07


def _render_history(records: list[SessionRecord]) -> None:
    if not records:
        console.print(Panel("No activity yet. Enter a command to start.", title="Recent Activity", border_style="bright_black"))
        return

    rows = []
    for record in records[:5]:
        rows.append(
            Panel(
                f"[bold]{record.instruction}[/bold]\n{record.summary}\n\n[dim]{record.shell} • {record.status}[/dim]",
                border_style="magenta" if record.status == "blocked" else "green",
            )
        )
    console.print(Panel(Columns(rows, expand=True), title="Recent Activity", border_style="bright_black"))


def _launch_web_ui(host: str, port: int, open_browser: bool) -> None:
    if open_browser:
        webbrowser.open(f"http://{host}:{port}")
    from uvicorn import run as uvicorn_run

    uvicorn_run("app.main:app", host=host, port=port, reload=False)


def _show_online_menu(host: str, port: int) -> None:
    console.print(Panel.fit("[bold green]Go online[/bold green]", border_style="green"))
    console.print("[cyan]1.[/cyan] Web UI")
    console.print("[cyan]2.[/cyan] View in browser")
    console.print("[cyan]3.[/cyan] Back")

    choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")
    if choice == "1":
        console.print(f"[green]Starting web UI on http://{host}:{port}[/green]")
        _launch_web_ui(host, port, open_browser=False)
    elif choice == "2":
        console.print(f"[green]Opening browser view for http://{host}:{port}[/green]")
        _launch_web_ui(host, port, open_browser=True)


def _show_offline_menu() -> SessionConfig:
<<<<<<< HEAD
    pass
=======
    console.print(Panel.fit("[bold yellow]Stay offline[/bold yellow]", border_style="yellow"))
    console.print("[cyan]1.[/cyan] Continue with terminal")
    console.print("[cyan]2.[/cyan] Continue as administrator")
    console.print("[cyan]3.[/cyan] Open a native Windows terminal")
    console.print("[cyan]4.[/cyan] Back")

    choice = Prompt.ask("Choose", choices=["1", "2", "3", "4"], default="1")
    if choice == "2":
        if _relaunch_as_admin():
            raise SystemExit(0)
    if choice == "3":
        if _run_in_native_terminal(["--launcher", "--terminal"]):
            raise SystemExit(0)
    return SessionConfig()
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07


def _run_session(config: SessionConfig) -> None:
    service = CommandService()
    show_details = False
    records: list[SessionRecord] = []

<<<<<<< HEAD
    console.print("\n[bold cyan]J.A.R.V.I.S. Core Systems Interactive Mode[/bold cyan]")
    animated_print("[cyan]Awaiting absolute instructions.[/cyan]\n", 0.01)

    while True:
        try:
            raw = Prompt.ask("[bold white]You[/bold white]", default="").strip()
=======
    console.print(Panel.fit(f"[bold green]{HEADER}[/bold green]", border_style="green"))
    _render_mode_table(config)
    _render_quick_help()
    _render_status_strip(config, records)
    console.print(SEPARATOR)

    while True:
        try:
            raw = Prompt.ask(f"[{config.shell.value} | {'dry-run' if config.dry_run else 'live'}]", default="").strip()
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if not raw:
            continue

        if raw in {":quit", ":exit"}:
            break

        if raw == ":back":
            break

        if raw == ":history":
            _render_history(records)
            continue

        if raw.startswith(":shell"):
            parts = raw.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in {"powershell", "bash"}:
                config.shell = ShellType(parts[1])
                console.print(f"[yellow]Shell set to {config.shell.value}[/yellow]")
            else:
                console.print("[red]Usage: :shell powershell|bash[/red]")
            continue

        if raw.startswith(":dryrun"):
            parts = raw.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in {"on", "off"}:
                config.dry_run = parts[1] == "on"
                console.print(f"[yellow]Dry run is now {'on' if config.dry_run else 'off'}[/yellow]")
            else:
                console.print("[red]Usage: :dryrun on|off[/red]")
            continue

        if raw.startswith(":confirm"):
            parts = raw.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in {"on", "off"}:
                config.confirm_risky = parts[1] == "on"
                console.print(f"[yellow]Risk confirmation is now {'on' if config.confirm_risky else 'off'}[/yellow]")
            else:
                console.print("[red]Usage: :confirm on|off[/red]")
            continue

        if raw.startswith(":details"):
            parts = raw.split(maxsplit=1)
            if len(parts) == 2 and parts[1] in {"on", "off"}:
                show_details = parts[1] == "on"
                console.print(f"[yellow]Detailed output is now {'on' if show_details else 'off'}[/yellow]")
            else:
                console.print("[red]Usage: :details on|off[/red]")
            continue

        if raw == ":help":
            console.print(
                textwrap.dedent(
                    """
                    Commands:
                      :shell powershell|bash
                      :dryrun on|off
                      :confirm on|off
                      :back
                      :quit

                    Normal text is analyzed and shown as a command plan.
                    """
                ).strip()
            )
            continue

<<<<<<< HEAD
        with console.status("[bold bright_black]Connecting to systems...[/bold bright_black]", spinner="dots"):
            analysis = service.analyze(raw, config.shell)
            workflow = service.run(raw, config.shell, confirm_risky=config.confirm_risky, dry_run=config.dry_run)
=======
        analysis = service.analyze(raw, config.shell)
        workflow = service.run(raw, config.shell, confirm_risky=config.confirm_risky, dry_run=config.dry_run)
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07

        action_count = len(analysis.translation.actions)
        status_text = "blocked" if analysis.safety.blocked else ("needs confirmation" if analysis.safety.requires_confirmation else "ready")
        summary_text = f"{action_count} action{'s' if action_count != 1 else ''} • {status_text} • {round(analysis.translation.confidence * 100)}% confidence"
        records.insert(0, SessionRecord(instruction=raw, status=status_text, summary=summary_text, shell=config.shell.value))
        records[:] = records[:5]

<<<<<<< HEAD
        pass
        if analysis.translation.chat_response:
            console.print("\n[bold cyan]J.A.R.V.I.S:[/bold cyan] ", end="")
            animated_print(analysis.translation.chat_response, 0.02)
        else:
            console.print("\n[bold cyan]J.A.R.V.I.S:[/bold cyan] ", end="")
            animated_print("Protocol generated and initiating.", 0.02)

        if analysis.safety.blocked:
            console.print(f"\n[bold red][SYSTEM BLOCKED][/bold red] {analysis.safety.summary}")

        if workflow.execution is None:
            if not analysis.safety.blocked:
                console.print("\n[bold yellow]Execution held. Awaiting human confirmation.[/bold yellow]")
        elif workflow.execution.stderr:
            console.print(f"\n[bold red][SYSTEM ERROR][/bold red] {workflow.execution.stderr.strip()}\n")


def run_launcher(host: str = "127.0.0.1", port: int = 8000) -> None:
    os.system('cls' if os.name == 'nt' else 'clear')
    animated_print("[cyan]Initializing Core Systems...[/cyan]", 0.02)
    animated_print("[cyan]Loading Neural Pathways...[/cyan]", 0.02)
    animated_print("[cyan]Establishing secure link...[/cyan]", 0.02)
    time.sleep(0.5)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        _render_banner()
        console.print("\n[dim]Select Deployment Protocol:[/dim]\n")
        console.print("  [bold cyan][ 1 ][/bold cyan] Initialize Autonomous Terminal [dim](Standard)[/dim]")
        console.print("  [bold cyan][ 2 ][/bold cyan] Initialize Autonomous Terminal [dim](Administrator)[/dim]")
        console.print("  [bold cyan][ 3 ][/bold cyan] Deploy Holographic Web Core  [dim](HUD)[/dim]")
        console.print("  [bold cyan][ 4 ][/bold cyan] Initiate System Shutdown\n")

        choice = Prompt.ask("[bold]Protocol Override[/bold]", choices=["1", "2", "3", "4"], default="1")

        if choice == "1":
            _run_session(SessionConfig())
            continue

        if choice == "2":
            if _relaunch_as_admin():
                raise SystemExit(0)
            _run_session(SessionConfig())
            continue

        if choice == "3":
            _show_online_menu(host, port)
            continue

        if choice == "4":
            animated_print("[dim]Terminating connection...[/dim]", 0.02)
            break

=======
        console.print(SEPARATOR)
        _render_status_strip(config, records)
        if analysis.automation is not None:
            automation_lines = [
                f"Category: {analysis.automation.category.value}",
                f"Summary: {analysis.automation.summary}",
                f"Browser required: {'Yes' if analysis.automation.requires_browser else 'No'}",
                f"Admin required: {'Yes' if analysis.automation.requires_admin else 'No'}",
            ]
            if analysis.automation.notes:
                automation_lines.append(f"Notes: {'; '.join(analysis.automation.notes)}")
            console.print(Panel("\n".join(automation_lines), title="Automation", border_style="blue"))
        console.print(Panel.fit(
            f"[bold]Understood[/bold]\n{analysis.translation.original_text}\n\n"
            f"[bold]Actions[/bold]\n{action_count} planned step{'s' if action_count != 1 else ''}\n\n"
            f"[bold]Confidence[/bold] {round(analysis.translation.confidence * 100)}%",
            border_style="cyan",
            title="Natural Language",
        ))
        console.print(Panel.fit(
            f"[bold]Safety[/bold]\n{analysis.safety.summary}\n\n"
            f"[bold]Blocked[/bold] {'Yes' if analysis.safety.blocked else 'No'}\n"
            f"[bold]Confirmation[/bold] {'Yes' if analysis.safety.requires_confirmation else 'No'}",
            border_style="yellow",
            title="Safety Check",
        ))
        if workflow.execution is None:
            console.print(Panel("Execution skipped because the command was blocked or confirmation is required.", title="Execution", border_style="magenta"))
        else:
            execution_lines = [
                f"Status: {'Executed' if workflow.execution.executed else 'Pending'}",
                f"Message: {workflow.execution.message}",
            ]
            if workflow.execution.stdout:
                execution_lines.append(f"Output:\n{workflow.execution.stdout}")
            if workflow.execution.stderr:
                execution_lines.append(f"Errors:\n{workflow.execution.stderr}")
            console.print(Panel("\n\n".join(execution_lines), title="Execution", border_style="magenta"))

        if show_details:
            console.print(Panel.fit(
                json.dumps(dataclass_to_dict(analysis), indent=2),
                title="Details",
                border_style="bright_black",
            ))

        console.print(Panel(
            "[bold]What happened[/bold]\n"
            f"{raw}\n\n"
            f"[bold]Result[/bold] {summary_text}",
            border_style="bright_black",
            title="Summary",
        ))
        console.print(SEPARATOR)


def run_launcher(host: str = "127.0.0.1", port: int = 8000) -> None:
    while True:
        _render_banner()
        console.print("[cyan]1.[/cyan] Stay offline")
        console.print("[cyan]2.[/cyan] Go online")
        console.print("[cyan]3.[/cyan] Exit")

        choice = Prompt.ask("Choose", choices=["1", "2", "3"], default="1")

        if choice == "1":
            config = _show_offline_menu()
            _run_session(config)
            continue

        if choice == "2":
            _show_online_menu(host, port)
            continue

        if choice == "3":
            break


>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07
def run_cli() -> None:
    _run_session(SessionConfig())
