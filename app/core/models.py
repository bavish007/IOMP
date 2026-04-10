from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ShellType(str, Enum):
    powershell = "powershell"
    bash = "bash"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    blocked = "blocked"


class ExecutionProfile(str, Enum):
    safe = "safe"
    balanced = "balanced"
    power_user = "power_user"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    executed = "executed"


class AutomationCategory(str, Enum):
    system_setup = "system_setup"
    browser_automation = "browser_automation"
    desktop_automation = "desktop_automation"
    workflow_automation = "workflow_automation"


@dataclass(slots=True)
class AutomationStep:
    description: str
    commands: dict[ShellType, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def command_for(self, shell: ShellType) -> str | None:
        return self.commands.get(shell)


@dataclass(slots=True)
class AutomationPlan:
    category: AutomationCategory
    title: str
    summary: str
    steps: list[AutomationStep]
    requires_browser: bool = False
    requires_admin: bool = False
    requires_confirmation: bool = False
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)

    def command_lines(self, shell: ShellType) -> list[str]:
        return [command for step in self.steps if (command := step.command_for(shell))]


@dataclass(slots=True)
class CommandAction:
    description: str
    commands: dict[ShellType, str]
    risk_tags: list[str] = field(default_factory=list)

    def command_for(self, shell: ShellType) -> str:
        return self.commands[shell]


@dataclass(slots=True)
class TranslationResult:
    original_text: str
    normalized_text: str
    shell: ShellType
    actions: list[CommandAction]
    confidence: float
    notes: list[str] = field(default_factory=list)
<<<<<<< HEAD
    chat_response: str = ""
=======
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07

    def command_lines(self) -> list[str]:
        return [action.command_for(self.shell) for action in self.actions]


@dataclass(slots=True)
class SafetyIssue:
    level: RiskLevel
    reason: str
    command_index: int
    command: str


@dataclass(slots=True)
class SafetyReport:
    safe: bool
    requires_confirmation: bool
    blocked: bool
    issues: list[SafetyIssue] = field(default_factory=list)
    summary: str = ""


@dataclass(slots=True)
class ExecutionResult:
    executed: bool
    return_code: int | None
    stdout: str
    stderr: str
    command: str
    shell: ShellType
    dry_run: bool
    message: str
    steps: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class AnalysisResult:
    translation: TranslationResult
    safety: SafetyReport
    automation: AutomationPlan | None = None


@dataclass(slots=True)
class ApprovalStep:
    index: int
    description: str
    command: str
    shell: ShellType
    risk_level: RiskLevel
    requires_review: bool
    approved: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ApprovalRequest:
    id: str
    instruction: str
    shell: ShellType
    profile: ExecutionProfile
    status: ApprovalStatus
    created_at: str
    updated_at: str
    summary: str
    commands: list[str]
    steps: list[ApprovalStep]
    analysis: dict[str, Any]
    reason: str = ""
    dry_run: bool = True
    confirm_risky: bool = False


@dataclass(slots=True)
class WorkflowResult:
    analysis: AnalysisResult
    execution: ExecutionResult | None
    approval: ApprovalRequest | None = None


def dataclass_to_dict(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: dataclass_to_dict(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        }
    if isinstance(value, list):
        return [dataclass_to_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: dataclass_to_dict(item) for key, item in value.items()}
    return value
