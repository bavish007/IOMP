from __future__ import annotations

import re
from dataclasses import dataclass

from .models import AutomationCategory, AutomationPlan, AutomationStep, ShellType


_BROWSER_KEYWORDS = (
    "whatsapp",
    "telegram",
    "facebook",
    "instagram",
    "gmail",
    "youtube",
    "browser",
    "web",
    "website",
    "open app",
    "send a message",
    "send message",
    "message friend",
    "dm",
)

_SETUP_KEYWORDS = (
    "install python",
    "download python",
    "setup python",
    "set up python",
    "create venv",
    "virtual environment",
    "install package",
    "install requirements",
    "install dependencies",
    "upgrade pip",
    "update pip",
    "set path",
    "add to path",
    "environment setup",
    "bootstrap",
    "daily task",
    "daily tasks",
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_person_and_message(text: str) -> tuple[str, str]:
    person_match = re.search(r"(?:to|for)\s+([a-zA-Z][\w\s.-]{1,40}?)(?:\s+with|\s+saying|\s+that|\s+to|$)", text)
    message_match = re.search(r"(?:saying|message|text|with)\s+(.+)$", text)
    person = person_match.group(1).strip() if person_match else "a contact"
    message = message_match.group(1).strip() if message_match else "your message"
    return person, message


def _build_browser_plan(text: str) -> AutomationPlan:
    person, message = _extract_person_and_message(text)
    steps = [
        AutomationStep(
            description="Open WhatsApp Web in a browser",
            commands={
                ShellType.powershell: "Start-Process https://web.whatsapp.com",
                ShellType.bash: "xdg-open https://web.whatsapp.com || open https://web.whatsapp.com",
            },
            notes=["Login may be required before a message can be sent."],
        ),
        AutomationStep(
            description=f"Open chat for {person}",
            notes=["Browser automation runner required for this step."],
        ),
        AutomationStep(
            description=f"Send message: {message}",
            notes=["This step is intentionally separated from shell execution."],
        ),
    ]
    return AutomationPlan(
        category=AutomationCategory.browser_automation,
        title="Browser Automation",
        summary=f"Plan to automate a browser flow for {person} with the message '{message}'.",
        steps=steps,
        requires_browser=True,
        requires_confirmation=True,
        confidence=0.84,
        notes=["Use a browser automation runner such as Playwright for the message-sending steps."],
    )


def _build_system_setup_plan(text: str, shell: ShellType) -> AutomationPlan:
    steps: list[AutomationStep] = []
    normalized = _normalize(text)

    install_python = any(keyword in normalized for keyword in ("install python", "download python", "setup python", "set up python"))
    create_env = any(keyword in normalized for keyword in ("create venv", "virtual environment", "environment setup", "bootstrap"))
    install_packages = any(keyword in normalized for keyword in ("install package", "install requirements", "install dependencies"))
    update_path = "set path" in normalized or "add to path" in normalized
    update_pip = "upgrade pip" in normalized or "update pip" in normalized

    if install_python:
        steps.append(
            AutomationStep(
                description="Install Python",
                commands={
                    ShellType.powershell: "winget install -e --id Python.Python.3",
                    ShellType.bash: "sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip",
                },
                notes=["Choose the native package manager for the current platform."],
            )
        )

    if update_path:
        steps.append(
            AutomationStep(
                description="Refresh or update PATH for the current session",
                commands={
                    ShellType.powershell: "$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')",
                    ShellType.bash: 'export PATH="$HOME/.local/bin:$PATH"',
                },
                notes=["Persisted PATH updates should be reviewed before execution."],
            )
        )

    if create_env:
        steps.append(
            AutomationStep(
                description="Create a local virtual environment",
                commands={
                    ShellType.powershell: "python -m venv .venv",
                    ShellType.bash: "python3 -m venv .venv",
                },
            )
        )

    if update_pip:
        steps.append(
            AutomationStep(
                description="Upgrade pip",
                commands={
                    ShellType.powershell: ".\\.venv\\Scripts\\python -m pip install --upgrade pip",
                    ShellType.bash: "./.venv/bin/python -m pip install --upgrade pip",
                },
            )
        )

    if install_packages:
        steps.append(
            AutomationStep(
                description="Install project dependencies",
                commands={
                    ShellType.powershell: ".\\.venv\\Scripts\\python -m pip install -r requirements.txt",
                    ShellType.bash: "./.venv/bin/python -m pip install -r requirements.txt",
                },
            )
        )

    if not steps:
        steps.append(
            AutomationStep(
                description="Prepare a standard Python project environment",
                commands={
                    ShellType.powershell: "python -m venv .venv; .\\.venv\\Scripts\\python -m pip install -r requirements.txt",
                    ShellType.bash: "python3 -m venv .venv && ./.venv/bin/python -m pip install -r requirements.txt",
                },
            )
        )

    return AutomationPlan(
        category=AutomationCategory.system_setup,
        title="System Setup Automation",
        summary="Plan to install or prepare Python and the local project environment automatically.",
        steps=steps,
        requires_admin=install_python and shell == ShellType.powershell,
        requires_confirmation=install_python or update_path,
        confidence=0.89,
        notes=["This plan is intended for local machine bootstrap and dependency installation."],
    )


def _build_general_workflow_plan(text: str, shell: ShellType) -> AutomationPlan:
    normalized = _normalize(text)
    steps = [
        AutomationStep(
            description="Run the requested workflow as shell commands",
            commands={
                ShellType.powershell: text,
                ShellType.bash: text,
            },
        )
    ]
    return AutomationPlan(
        category=AutomationCategory.workflow_automation,
        title="Workflow Automation",
        summary=f"General automation plan derived from: {normalized}",
        steps=steps,
        requires_confirmation=False,
        confidence=0.72,
        notes=["Used when the instruction looks like an automation workflow rather than a simple command."],
    )


def build_automation_plan(instruction: str, shell: ShellType) -> AutomationPlan | None:
    normalized = _normalize(instruction)

    if any(keyword in normalized for keyword in _BROWSER_KEYWORDS):
        return _build_browser_plan(instruction)

    if any(keyword in normalized for keyword in _SETUP_KEYWORDS):
        return _build_system_setup_plan(instruction, shell)

    if any(keyword in normalized for keyword in ("automation", "workflow", "routine", "daily task", "daily tasks", "schedule")):
        return _build_general_workflow_plan(instruction, shell)

    return None
