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


def execute_command(command: str, shell: ShellType, dry_run: bool = True, timeout_seconds: int = 120) -> ExecutionResult:
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

    try:
        completed = subprocess.run(
            shell_prefix + [command],
            capture_output=True,
            text=False,
            timeout=timeout_seconds,
            check=False,
        )
        return_code = completed.returncode
        raw_stdout = completed.stdout or b""
        raw_stderr = completed.stderr or b""
        message = "Command executed successfully." if return_code == 0 else "Command completed with errors."
    except subprocess.TimeoutExpired as e:
        return_code = 124
        raw_stdout = e.stdout or b""
        raw_stderr = e.stderr or b""
        message = f"Command execution forcefully terminated after {timeout_seconds} seconds."

    # Prevent UTF-8 Decode crashes
    stdout_str = raw_stdout.decode("utf-8", errors="replace").strip()
    stderr_str = raw_stderr.decode("utf-8", errors="replace").strip()

    # Prevent RAM overflow from infinite log loops or large outputs
    max_len = 50000
    if len(stdout_str) > max_len:
        stdout_str = stdout_str[-max_len:] + "\n...[TRUNCATED FOR MEMORY SAFETY]"
    if len(stderr_str) > max_len:
        stderr_str = stderr_str[-max_len:] + "\n...[TRUNCATED FOR MEMORY SAFETY]"

    return ExecutionResult(
        executed=True,
        return_code=return_code,
        stdout=stdout_str,
        stderr=stderr_str,
        command=command,
        shell=shell,
        dry_run=False,
        message=message,
        steps=[
            {
                "command": command,
                "return_code": return_code,
                "stdout": stdout_str,
                "stderr": stderr_str,
            }
        ],
    )


def execute_commands(commands: list[str], shell: ShellType, dry_run: bool = True, timeout_seconds: int = 120) -> ExecutionResult:
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
