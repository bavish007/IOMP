from __future__ import annotations

import shutil
import subprocess
from typing import Any

from .models import ExecutionResult, ShellType


def _resolve_shell(shell: ShellType) -> list[str] | None:
    if shell == ShellType.bash:
        if shutil.which("bash"):
            return ["bash", "-lc"]
        return None

    candidates = ["pwsh", "powershell", "powershell.exe"]
    for candidate in candidates:
        if shutil.which(candidate):
            if candidate == "powershell.exe":
                return [candidate, "-NoProfile", "-Command"]
            return [candidate, "-NoProfile", "-Command"]
    return None


def execute_command(command: str, shell: ShellType, dry_run: bool = True, timeout_seconds: int = 30) -> ExecutionResult:
    if dry_run:
        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command=command,
            shell=shell,
            dry_run=True,
            message="Dry run mode: command was not executed.",
        )

    shell_prefix = _resolve_shell(shell)
    if shell_prefix is None:
        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command=command,
            shell=shell,
            dry_run=False,
            message=f"No executable shell found for {shell.value}.",
        )

    completed = subprocess.run(
        shell_prefix + [command],
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return ExecutionResult(
        executed=True,
        return_code=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        command=command,
        shell=shell,
        dry_run=False,
        message="Command executed successfully." if completed.returncode == 0 else "Command completed with errors.",
        steps=[
            {
                "command": command,
                "return_code": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        ],
    )


def execute_commands(commands: list[str], shell: ShellType, dry_run: bool = True, timeout_seconds: int = 30) -> ExecutionResult:
    if not commands:
        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command="",
            shell=shell,
            dry_run=dry_run,
            message="No commands to execute.",
            steps=[],
        )

    if dry_run:
        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command=(" && ".join(commands) if shell == ShellType.bash else "; ".join(commands)),
            shell=shell,
            dry_run=True,
            message="Dry run mode: command plan was not executed.",
            steps=[{"command": command, "dry_run": True} for command in commands],
        )

    step_results: list[dict[str, Any]] = []
    full_stdout: list[str] = []
    full_stderr: list[str] = []
    for command in commands:
        step = execute_command(command=command, shell=shell, dry_run=False, timeout_seconds=timeout_seconds)
        step_results.append(
            {
                "command": command,
                "return_code": step.return_code,
                "stdout": step.stdout,
                "stderr": step.stderr,
            }
        )
        if step.stdout:
            full_stdout.append(step.stdout)
        if step.stderr:
            full_stderr.append(step.stderr)
        if step.return_code not in (0, None):
            return ExecutionResult(
                executed=True,
                return_code=step.return_code,
                stdout="\n".join(full_stdout),
                stderr="\n".join(full_stderr),
                command=(" && ".join(commands) if shell == ShellType.bash else "; ".join(commands)),
                shell=shell,
                dry_run=False,
                message="Command plan stopped after a step failed.",
                steps=step_results,
            )

    return ExecutionResult(
        executed=True,
        return_code=0,
        stdout="\n".join(full_stdout),
        stderr="\n".join(full_stderr),
        command=(" && ".join(commands) if shell == ShellType.bash else "; ".join(commands)),
        shell=shell,
        dry_run=False,
        message="Command plan executed successfully.",
        steps=step_results,
    )
