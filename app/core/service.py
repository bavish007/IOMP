from __future__ import annotations

from .browser import execute_browser_plan
from .executor import execute_commands
from .approval import approve_request, create_request, deny_request, get_request, list_requests, mark_executed
from .models import ApprovalRequest, ApprovalStep, AnalysisResult, ApprovalStatus, AutomationCategory, CommandAction, ExecutionProfile, ExecutionResult, RiskLevel, SafetyIssue, SafetyReport, ShellType, TranslationResult, WorkflowResult, dataclass_to_dict
from .automation import build_automation_plan
from .audit import record_event
from .learning import find_best_match, record_success
from .policy import apply_execution_profile
from .safety import assess_safety
from .translator import translate_instruction


class CommandService:
    def _build_approval_steps(self, analysis: AnalysisResult, shell: ShellType) -> list[ApprovalStep]:
        issues_by_index: dict[int, list[SafetyIssue]] = {}
        for issue in analysis.safety.issues:
            issues_by_index.setdefault(issue.command_index, []).append(issue)

        if analysis.automation is not None:
            steps: list[ApprovalStep] = []
            for index, automation_step in enumerate(analysis.automation.steps):
                command = automation_step.command_for(shell) or ""
                step_issues = issues_by_index.get(index, [])
                risk_level = RiskLevel.low
                if any(issue.level == RiskLevel.blocked for issue in step_issues):
                    risk_level = RiskLevel.blocked
                elif any(issue.level == RiskLevel.high for issue in step_issues):
                    risk_level = RiskLevel.high
                elif step_issues or analysis.automation.requires_confirmation or analysis.automation.requires_admin:
                    risk_level = RiskLevel.medium

                requires_review = (
                    analysis.safety.requires_confirmation
                    or analysis.safety.blocked
                    or analysis.automation.requires_confirmation
                    or analysis.automation.requires_admin
                    or bool(step_issues)
                    or not command
                )

                steps.append(
                    ApprovalStep(
                        index=index,
                        description=automation_step.description,
                        command=command,
                        shell=shell,
                        risk_level=risk_level,
                        requires_review=requires_review,
                        approved=not requires_review,
                        notes=list(automation_step.notes),
                    )
                )
            return steps

        steps = []
        for index, action in enumerate(analysis.translation.actions):
            command = action.command_for(shell)
            step_issues = issues_by_index.get(index, [])
            risk_level = RiskLevel.low
            if any(issue.level == RiskLevel.blocked for issue in step_issues):
                risk_level = RiskLevel.blocked
            elif any(issue.level == RiskLevel.high for issue in step_issues):
                risk_level = RiskLevel.high
            elif step_issues or analysis.safety.requires_confirmation:
                risk_level = RiskLevel.medium

            requires_review = analysis.safety.requires_confirmation or bool(step_issues)
            steps.append(
                ApprovalStep(
                    index=index,
                    description=action.description,
                    command=command,
                    shell=shell,
                    risk_level=risk_level,
                    requires_review=requires_review,
                    approved=not requires_review,
                    notes=list(action.risk_tags),
                )
            )

        return steps

    def _queue_approval(
        self,
        instruction: str,
        analysis: AnalysisResult,
        shell: ShellType,
        profile: ExecutionProfile,
        dry_run: bool,
        confirm_risky: bool,
    ) -> ApprovalRequest:
        commands = analysis.automation.command_lines(shell) if analysis.automation is not None else analysis.translation.command_lines()
        steps = self._build_approval_steps(analysis, shell)
        request = create_request(
            instruction=instruction,
            shell=shell,
            profile=profile,
            summary=analysis.safety.summary,
            commands=commands,
            steps=steps,
            analysis=dataclass_to_dict(analysis),
            dry_run=dry_run,
            confirm_risky=confirm_risky,
            reason=analysis.safety.summary,
        )
        record_event(
            "approval_queue",
            {
                "approval_id": request.id,
                "instruction": instruction,
                "shell": shell.value,
                "profile": profile.value,
                "step_count": len(request.steps),
                "command_count": len(request.commands),
            },
        )
        return request

    def analyze(self, instruction: str, shell: ShellType, profile: ExecutionProfile = ExecutionProfile.balanced) -> AnalysisResult:
        learned = find_best_match(instruction, shell)
        if learned is not None:
            translation = TranslationResult(
                original_text=instruction,
                normalized_text=learned.normalized_instruction,
                shell=shell,
                actions=[],
                confidence=min(0.8 + (learned.success_count / 20.0), 0.98),
                notes=[f"Reused from successful history ({learned.success_count} runs)."],
            )
            translation.actions = [
                CommandAction(
                    description="Learned command plan",
                    commands={current_shell: command for current_shell in ShellType},
                )
                for command in learned.commands
            ]
            safety = assess_safety(translation.command_lines())
            safety = apply_execution_profile(safety, profile)
            result = AnalysisResult(translation=translation, safety=safety, automation=None)
            record_event(
                "analyze",
                {
                    "instruction": instruction,
                    "shell": shell.value,
                    "profile": profile.value,
                    "source": "learned",
                    "safe": safety.safe,
                    "requires_confirmation": safety.requires_confirmation,
                    "blocked": safety.blocked,
                },
            )
            return result

        translation = translate_instruction(instruction, shell)
        automation = build_automation_plan(instruction, shell)

        if automation is not None:
            automation_commands = automation.command_lines(shell)
            if automation_commands:
                safety = assess_safety(automation_commands)
            else:
                safety = assess_safety(translation.command_lines())

            if automation.requires_confirmation or automation.requires_admin:
                safety = SafetyReport(
                    safe=False,
                    requires_confirmation=True,
                    blocked=False,
                    issues=safety.issues
                    + [
                        SafetyIssue(
                            level=RiskLevel.medium,
                            reason="Automation plan requires review before execution.",
                            command_index=0,
                            command=automation.title,
                        )
                    ],
                    summary=f"{automation.title} is ready for review.",
                )

            safety = apply_execution_profile(safety, profile, automation)
            result = AnalysisResult(translation=translation, safety=safety, automation=automation)
            record_event(
                "analyze",
                {
                    "instruction": instruction,
                    "shell": shell.value,
                    "profile": profile.value,
                    "source": "automation" if automation else "rules",
                    "safe": safety.safe,
                    "requires_confirmation": safety.requires_confirmation,
                    "blocked": safety.blocked,
                },
            )
            return result

        safety = assess_safety(translation.command_lines())
        safety = apply_execution_profile(safety, profile)
        result = AnalysisResult(translation=translation, safety=safety, automation=None)
        record_event(
            "analyze",
            {
                "instruction": instruction,
                "shell": shell.value,
                "profile": profile.value,
                "source": "rules",
                "safe": safety.safe,
                "requires_confirmation": safety.requires_confirmation,
                "blocked": safety.blocked,
            },
        )
        return result

    def run(
        self,
        instruction: str,
        shell: ShellType,
        confirm_risky: bool = False,
        dry_run: bool = True,
        profile: ExecutionProfile = ExecutionProfile.balanced,
    ) -> WorkflowResult:
        analysis = self.analyze(instruction, shell, profile=profile)
        if analysis.safety.blocked:
            record_event(
                "run",
                {
                    "instruction": instruction,
                    "shell": shell.value,
                    "profile": profile.value,
                    "status": "blocked",
                },
            )
            return WorkflowResult(analysis=analysis, execution=None)

        if analysis.safety.requires_confirmation and not confirm_risky:
            approval = self._queue_approval(
                instruction=instruction,
                analysis=analysis,
                shell=shell,
                profile=profile,
                dry_run=dry_run,
                confirm_risky=confirm_risky,
            )
            record_event(
                "run",
                {
                    "instruction": instruction,
                    "shell": shell.value,
                    "profile": profile.value,
                    "status": "pending_confirmation",
                    "approval_id": approval.id,
                    "step_count": len(approval.steps),
                },
            )
            return WorkflowResult(analysis=analysis, execution=None, approval=approval)

        command_lines = analysis.translation.command_lines()
        if analysis.automation is not None:
            if analysis.automation.category == AutomationCategory.browser_automation:
                execution = execute_browser_plan(analysis.automation, shell=shell, dry_run=dry_run)
                record_event(
                    "run",
                    {
                        "instruction": instruction,
                        "shell": shell.value,
                        "profile": profile.value,
                        "status": "executed" if execution.executed else "dry_run",
                        "command_count": len(analysis.automation.steps),
                        "return_code": execution.return_code,
                        "automation_category": analysis.automation.category.value,
                    },
                )
                return WorkflowResult(analysis=analysis, execution=execution)

            automation_commands = analysis.automation.command_lines(shell)
            if automation_commands:
                command_lines = automation_commands

        execution = execute_commands(commands=command_lines, shell=shell, dry_run=dry_run)

        if execution.executed and execution.return_code == 0 and not dry_run:
            record_success(instruction=instruction, shell=shell, commands=command_lines)

        record_event(
            "run",
            {
                "instruction": instruction,
                "shell": shell.value,
                "profile": profile.value,
                "status": "executed" if execution.executed else "dry_run",
                "command_count": len(command_lines),
                "return_code": execution.return_code,
            },
        )

        return WorkflowResult(analysis=analysis, execution=execution)

    def list_approvals(self, status: ApprovalStatus | None = None) -> list[ApprovalRequest]:
        return list_requests(status)

    def get_approval(self, request_id: str) -> ApprovalRequest | None:
        return get_request(request_id)

    def approve_approval(
        self,
        request_id: str,
        step_indexes: list[int] | None = None,
        execute_after: bool = False,
        dry_run: bool | None = None,
    ) -> tuple[ApprovalRequest, ExecutionResult | None]:
        request = approve_request(request_id, step_indexes=step_indexes)
        execution = None

        if request.status == ApprovalStatus.approved and execute_after:
            should_dry_run = request.dry_run if dry_run is None else dry_run
            if request.commands:
                execution = execute_commands(commands=request.commands, shell=request.shell, dry_run=should_dry_run)
                if execution.executed and execution.return_code == 0 and not should_dry_run:
                    record_success(instruction=request.instruction, shell=request.shell, commands=request.commands)
                request = mark_executed(request.id)
                record_event(
                    "approval_execute",
                    {
                        "approval_id": request.id,
                        "instruction": request.instruction,
                        "shell": request.shell.value,
                        "dry_run": should_dry_run,
                        "return_code": execution.return_code,
                    },
                )
            else:
                execution = execute_commands(commands=[], shell=request.shell, dry_run=should_dry_run)

        record_event(
            "approval_review",
            {
                "approval_id": request.id,
                "instruction": request.instruction,
                "shell": request.shell.value,
                "status": request.status.value,
                "execute_after": execute_after,
            },
        )
        return request, execution

    def deny_approval(self, request_id: str, reason: str = "") -> ApprovalRequest:
        request = deny_request(request_id, reason=reason)
        record_event(
            "approval_deny",
            {
                "approval_id": request.id,
                "instruction": request.instruction,
                "shell": request.shell.value,
                "reason": reason,
            },
        )
        return request
