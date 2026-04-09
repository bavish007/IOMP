from __future__ import annotations

from .executor import execute_command
from .models import AutomationPlan, AutomationStep, ExecutionResult, ShellType


def _step_record(step: AutomationStep, shell: ShellType, index: int, status: str, command: str = "", stdout: str = "", stderr: str = "", return_code: int | None = None) -> dict[str, object]:
    return {
        "index": index,
        "description": step.description,
        "command": command,
        "shell": shell.value,
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": return_code,
        "notes": list(step.notes),
    }


def execute_browser_plan(plan: AutomationPlan, shell: ShellType, dry_run: bool = True, timeout_seconds: int = 30) -> ExecutionResult:
    if not plan.steps:
        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command=plan.title,
            shell=shell,
            dry_run=dry_run,
            message="No browser steps were generated.",
            steps=[],
        )

    first_step = plan.steps[0]
    first_command = first_step.command_for(shell) or ""
    step_records: list[dict[str, object]] = []

    if dry_run:
        if first_command:
            step_records.append(_step_record(first_step, shell, 0, "planned", command=first_command))
        else:
            step_records.append(_step_record(first_step, shell, 0, "manual", command="", stdout="Browser automation runner required."))

        for index, step in enumerate(plan.steps[1:], start=1):
            command = step.command_for(shell) or ""
            note = "Manual browser interaction required." if not command else "Browser automation runner required for this step."
            step_records.append(_step_record(step, shell, index, "manual", command=command, stdout=note))

        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command=first_command or plan.title,
            shell=shell,
            dry_run=True,
            message="Browser automation plan prepared in dry-run mode.",
            steps=step_records,
        )

    if not first_command:
        for index, step in enumerate(plan.steps):
            step_records.append(
                _step_record(
                    step,
                    shell,
                    index,
                    "manual",
                    command=step.command_for(shell) or "",
                    stdout="Browser automation runner required for execution.",
                )
            )
        return ExecutionResult(
            executed=False,
            return_code=None,
            stdout="",
            stderr="",
            command=plan.title,
            shell=shell,
            dry_run=False,
            message="Browser automation runner required to continue.",
            steps=step_records,
        )

    first_execution = execute_command(first_command, shell, dry_run=False, timeout_seconds=timeout_seconds)
    step_records.append(
        _step_record(
            first_step,
            shell,
            0,
            "executed" if first_execution.executed and first_execution.return_code == 0 else "failed",
            command=first_command,
            stdout=first_execution.stdout,
            stderr=first_execution.stderr,
            return_code=first_execution.return_code,
        )
    )

    for index, step in enumerate(plan.steps[1:], start=1):
        command = step.command_for(shell) or ""
        step_records.append(
            _step_record(
                step,
                shell,
                index,
                "manual",
                command=command,
                stdout="Manual browser interaction required for this step.",
                stderr="",
                return_code=None,
            )
        )

    return ExecutionResult(
        executed=first_execution.executed,
        return_code=first_execution.return_code,
        stdout=first_execution.stdout,
        stderr=first_execution.stderr,
        command=first_command,
        shell=shell,
        dry_run=False,
        message="Browser workflow launched; remaining steps require browser automation support or manual completion.",
        steps=step_records,
    )