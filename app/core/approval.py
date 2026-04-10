from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import ApprovalRequest, ApprovalStatus, ApprovalStep, ExecutionProfile, RiskLevel, ShellType, dataclass_to_dict


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
APPROVAL_FILE = DATA_DIR / "approvals.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not APPROVAL_FILE.exists():
        APPROVAL_FILE.write_text("[]\n", encoding="utf-8")


def _load_raw() -> list[dict[str, object]]:
    _ensure_store()
    try:
        raw = json.loads(APPROVAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    return raw if isinstance(raw, list) else []


def _step_from_payload(payload: dict[str, object]) -> ApprovalStep:
    return ApprovalStep(
        index=int(payload.get("index", 0)),
        description=str(payload.get("description", "")),
        command=str(payload.get("command", "")),
        shell=ShellType(str(payload.get("shell", ShellType.powershell.value))),
        risk_level=RiskLevel(str(payload.get("risk_level", RiskLevel.medium.value))),
        requires_review=bool(payload.get("requires_review", True)),
        approved=bool(payload.get("approved", False)),
        notes=[str(note) for note in payload.get("notes", [])],
    )


def _request_from_payload(payload: dict[str, object]) -> ApprovalRequest:
    analysis_payload = payload.get("analysis", {})
    return ApprovalRequest(
        id=str(payload.get("id", "")),
        instruction=str(payload.get("instruction", "")),
        shell=ShellType(str(payload.get("shell", ShellType.powershell.value))),
        profile=ExecutionProfile(str(payload.get("profile", ExecutionProfile.balanced.value))),
        status=ApprovalStatus(str(payload.get("status", ApprovalStatus.pending.value))),
        created_at=str(payload.get("created_at", _now())),
        updated_at=str(payload.get("updated_at", _now())),
        summary=str(payload.get("summary", "")),
        commands=[str(command) for command in payload.get("commands", [])],
        steps=[_step_from_payload(step) for step in payload.get("steps", [])],
        analysis=analysis_payload if isinstance(analysis_payload, dict) else {},
        reason=str(payload.get("reason", "")),
        dry_run=bool(payload.get("dry_run", True)),
        confirm_risky=bool(payload.get("confirm_risky", False)),
    )


def _request_to_payload(request: ApprovalRequest) -> dict[str, object]:
    payload = dataclass_to_dict(request)
    payload["shell"] = request.shell.value
    payload["profile"] = request.profile.value
    payload["status"] = request.status.value
    for step in payload.get("steps", []):
        if isinstance(step, dict):
            step["shell"] = str(step.get("shell", ShellType.powershell.value))
            step["risk_level"] = str(step.get("risk_level", "medium"))
    return payload


def _save_all(requests: list[ApprovalRequest]) -> None:
    payload = [_request_to_payload(item) for item in requests]
    APPROVAL_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _load_all() -> list[ApprovalRequest]:
    return [_request_from_payload(item) for item in _load_raw()]


def list_requests(status: ApprovalStatus | None = None) -> list[ApprovalRequest]:
    items = _load_all()
    if status is None:
        return sorted(items, key=lambda item: item.created_at, reverse=True)
    return sorted([item for item in items if item.status == status], key=lambda item: item.created_at, reverse=True)


def get_request(request_id: str) -> ApprovalRequest | None:
    for request in _load_all():
        if request.id == request_id:
            return request
    return None


def create_request(
    *,
    instruction: str,
    shell: ShellType,
    profile: ExecutionProfile,
    summary: str,
    commands: list[str],
    steps: list[ApprovalStep],
    analysis: dict[str, object],
    dry_run: bool,
    confirm_risky: bool,
    reason: str = "",
) -> ApprovalRequest:
    request = ApprovalRequest(
        id=str(uuid4()),
        instruction=instruction,
        shell=shell,
        profile=profile,
        status=ApprovalStatus.pending,
        created_at=_now(),
        updated_at=_now(),
        summary=summary,
        commands=commands,
        steps=steps,
        analysis=analysis,
        reason=reason,
        dry_run=dry_run,
        confirm_risky=confirm_risky,
    )

    requests = _load_all()
    requests.append(request)
    _save_all(requests)
    return request


def update_request(request: ApprovalRequest) -> ApprovalRequest:
    requests = _load_all()
    updated = False
    for index, existing in enumerate(requests):
        if existing.id == request.id:
            requests[index] = request
            updated = True
            break
    if not updated:
        requests.append(request)
    _save_all(requests)
    return request


def approve_request(request_id: str, step_indexes: list[int] | None = None) -> ApprovalRequest:
    request = get_request(request_id)
    if request is None:
        raise KeyError(request_id)

    if request.status == ApprovalStatus.denied:
        raise ValueError("Approval request has been denied.")

    if step_indexes is None or not step_indexes:
        for step in request.steps:
            if step.requires_review:
                step.approved = True
    else:
        allowed_indexes = set(step_indexes)
        for step in request.steps:
            if step.index in allowed_indexes:
                step.approved = True

    if all(step.approved or not step.requires_review for step in request.steps):
        request.status = ApprovalStatus.approved
    else:
        request.status = ApprovalStatus.pending

    request.updated_at = _now()
    return update_request(request)


def deny_request(request_id: str, reason: str = "") -> ApprovalRequest:
    request = get_request(request_id)
    if request is None:
        raise KeyError(request_id)

    request.status = ApprovalStatus.denied
    request.reason = reason
    request.updated_at = _now()
    return update_request(request)


def mark_executed(request_id: str) -> ApprovalRequest:
    request = get_request(request_id)
    if request is None:
        raise KeyError(request_id)

    request.status = ApprovalStatus.executed
    request.updated_at = _now()
    return update_request(request)