from __future__ import annotations

import re

from .models import RiskLevel, SafetyIssue, SafetyReport


BLOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(format|diskpart|bcdedit|shutdown|restart-computer|stop-computer)\b", re.I), "Potentially destructive system command."),
    (re.compile(r"\brm\s+-rf\s+/", re.I), "Recursive root deletion is blocked."),
    (re.compile(r"\bremove-item\b.*-recurse\b", re.I), "Recursive removal is blocked."),
    (re.compile(r"\bdel\b.*\b/s\b", re.I), "Recursive deletion is blocked."),
    (re.compile(r"\breg\s+delete\b", re.I), "Registry deletion is blocked."),
]

CONFIRM_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(remove-item|rm|del|erase|rmdir)\b", re.I), "Deletion commands require confirmation."),
    (re.compile(r"\b(move-item|mv)\b", re.I), "Moves can overwrite files or change locations."),
    (re.compile(r"\b(copy-item|cp)\b", re.I), "Copy operations may overwrite existing files."),
    (re.compile(r"\b(stop-process|taskkill|kill|pkill)\b", re.I), "Process termination requires confirmation."),
]

SENSITIVE_PATHS = [
    r"c:\windows",
    r"c:\program files",
    r"c:\program files (x86)",
    r"/etc",
    r"/bin",
    r"/usr",
    r"/var/lib",
    r"/root",
]


def assess_safety(commands: list[str]) -> SafetyReport:
    issues: list[SafetyIssue] = []
    blocked = False
    requires_confirmation = False

    for index, command in enumerate(commands):
        lowered = command.lower()

        for pattern, reason in BLOCK_PATTERNS:
            if pattern.search(lowered):
                issues.append(
                    SafetyIssue(
                        level=RiskLevel.blocked,
                        reason=reason,
                        command_index=index,
                        command=command,
                    )
                )
                blocked = True

        if any(path in lowered for path in SENSITIVE_PATHS):
            issues.append(
                SafetyIssue(
                    level=RiskLevel.high,
                    reason="Command targets a sensitive system path.",
                    command_index=index,
                    command=command,
                )
            )
            blocked = True

        if re.search(r"\b(remove-item|rm|del|erase|rmdir)\b", lowered):
            requires_confirmation = True

        if re.search(r"\b(move-item|mv|copy-item|cp)\b", lowered):
            requires_confirmation = True

        if re.search(r"\b(stop-process|taskkill|kill|pkill)\b", lowered):
            requires_confirmation = True

        if re.search(r"\b(remove-item|rm|del)\b.*\*", lowered):
            issues.append(
                SafetyIssue(
                    level=RiskLevel.medium,
                    reason="Wildcard deletion affects multiple files.",
                    command_index=index,
                    command=command,
                )
            )
            requires_confirmation = True

        for pattern, reason in CONFIRM_PATTERNS:
            if pattern.search(lowered):
                issues.append(
                    SafetyIssue(
                        level=RiskLevel.medium,
                        reason=reason,
                        command_index=index,
                        command=command,
                    )
                )

    safe = not blocked and not issues
    return SafetyReport(
        safe=safe,
        requires_confirmation=requires_confirmation and not blocked,
        blocked=blocked,
        issues=issues,
        summary=(
            "Execution blocked by safety policy."
            if blocked
            else (
                "Execution requires confirmation."
                if requires_confirmation
                else "No safety issues detected."
            )
        ),
    )
