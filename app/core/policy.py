from __future__ import annotations

from dataclasses import replace

from .models import AutomationPlan, ExecutionProfile, RiskLevel, SafetyIssue, SafetyReport


def apply_execution_profile(
    safety: SafetyReport,
    profile: ExecutionProfile,
    automation: AutomationPlan | None = None,
) -> SafetyReport:
    if profile == ExecutionProfile.balanced:
        return safety

    issues = list(safety.issues)
    summary = safety.summary
    blocked = safety.blocked
    requires_confirmation = safety.requires_confirmation

    if profile == ExecutionProfile.safe:
        if not blocked:
            requires_confirmation = True
        if automation is not None:
            issues.append(
                SafetyIssue(
                    level=RiskLevel.medium,
                    reason="Safe profile requires explicit approval for automation plans.",
                    command_index=0,
                    command=automation.title,
                )
            )
            requires_confirmation = True
            summary = f"{automation.title} is queued for manual approval."
        else:
            summary = summary or "Safe profile is waiting for approval."

    elif profile == ExecutionProfile.power_user:
        if not blocked:
            requires_confirmation = False
        if automation is not None and automation.requires_browser:
            requires_confirmation = True
            summary = f"{automation.title} requires a browser runner." 
        if automation is not None and automation.requires_admin:
            requires_confirmation = True
            issues.append(
                SafetyIssue(
                    level=RiskLevel.medium,
                    reason="Automation requires elevated privileges.",
                    command_index=0,
                    command=automation.title,
                )
            )

    return replace(
        safety,
        issues=issues,
        requires_confirmation=requires_confirmation and not blocked,
        blocked=blocked,
        safe=not blocked and not issues,
        summary=summary,
    )
