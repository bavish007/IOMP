from __future__ import annotations

from collections import deque
from pathlib import Path
from time import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()
from pydantic import BaseModel, Field
from starlette.requests import Request

from .core.models import ApprovalStatus, ExecutionProfile, ShellType, dataclass_to_dict
from .core.ai import ai_is_available
from .core.audit import list_events
from .core.learning import list_learned, record_success
from .core.service import CommandService


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"

app = FastAPI(title="Talk2Shell", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
service = CommandService()
history: deque[dict[str, object]] = deque(maxlen=25)


class AnalyzeRequest(BaseModel):
    instruction: str = Field(min_length=1)
    shell: ShellType = ShellType.powershell
    profile: ExecutionProfile = ExecutionProfile.balanced


class RunRequest(BaseModel):
    instruction: str = Field(min_length=1)
    shell: ShellType = ShellType.powershell
    confirm_risky: bool = False
    dry_run: bool = True
    profile: ExecutionProfile = ExecutionProfile.balanced


class ApprovalReviewRequest(BaseModel):
    step_indexes: list[int] = Field(default_factory=list)
    execute_after: bool = False
    dry_run: bool | None = None


class ApprovalDenyRequest(BaseModel):
    reason: str = ""


class FeedbackRequest(BaseModel):
    instruction: str = Field(min_length=1)
    shell: ShellType = ShellType.powershell
    commands: list[str] = Field(min_length=1)


def _store_history(entry: dict[str, object]) -> None:
    history.appendleft(entry)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_name": "Talk2Shell",
        },
    )


@app.post("/api/analyze")
def analyze(payload: AnalyzeRequest) -> JSONResponse:
    result = service.analyze(payload.instruction, payload.shell, profile=payload.profile)
    response = dataclass_to_dict(result)
    _store_history(
        {
            "type": "analyze",
            "timestamp": time(),
            "instruction": payload.instruction,
            "shell": payload.shell.value,
            "result": response,
        }
    )
    return JSONResponse(response)


@app.post("/api/run")
def run(payload: RunRequest) -> JSONResponse:
    result = service.run(
        instruction=payload.instruction,
        shell=payload.shell,
        confirm_risky=payload.confirm_risky,
        dry_run=payload.dry_run,
        profile=payload.profile,
    )
    if result.execution is None and result.analysis.safety.blocked:
        raise HTTPException(status_code=400, detail=result.analysis.safety.summary())

    response = dataclass_to_dict(result)
    _store_history(
        {
            "type": "run",
            "timestamp": time(),
            "instruction": payload.instruction,
            "shell": payload.shell.value,
            "result": response,
        }
    )
    if result.approval is not None:
        return JSONResponse(response, status_code=409)
    return JSONResponse(response)


@app.get("/api/history")
def get_history() -> JSONResponse:
    return JSONResponse({"items": list(history)})


@app.post("/api/feedback")
def feedback(payload: FeedbackRequest) -> JSONResponse:
    record_success(
        instruction=payload.instruction,
        shell=payload.shell,
        commands=payload.commands,
    )
    return JSONResponse({"ok": True})


@app.get("/api/learned")
def get_learned(shell: ShellType | None = None) -> JSONResponse:
    items = list_learned(shell)
    response = [
        {
            "instruction": item.instruction,
            "normalized_instruction": item.normalized_instruction,
            "shell": item.shell.value,
            "commands": item.commands,
            "success_count": item.success_count,
        }
        for item in items
    ]
    return JSONResponse({"items": response})


@app.get("/api/capabilities")
def get_capabilities() -> JSONResponse:
    learned_count = len(list_learned())
    approval_count = len(service.list_approvals(ApprovalStatus.pending))
    return JSONResponse(
        {
            "ai_available": ai_is_available(),
            "learned_count": learned_count,
            "pending_approvals": approval_count,
            "automation_categories": [
                "system_setup",
                "browser_automation",
                "desktop_automation",
                "workflow_automation",
            ],
        }
    )


@app.get("/api/audit")
def get_audit(limit: int = 50) -> JSONResponse:
    events = list_events(limit=limit)
    response = [
        {
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "payload": event.payload,
        }
        for event in events
    ]
    return JSONResponse({"items": response})



@app.get("/api/approvals")
def get_approvals(status: ApprovalStatus | None = None) -> JSONResponse:
    items = service.list_approvals(status)
    return JSONResponse({"items": [dataclass_to_dict(item) for item in items]})


@app.get("/api/approvals/{approval_id}")
def get_approval(approval_id: str) -> JSONResponse:
    request = service.get_approval(approval_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return JSONResponse(dataclass_to_dict(request))


@app.post("/api/approvals/{approval_id}/approve")
def approve_approval(approval_id: str, payload: ApprovalReviewRequest) -> JSONResponse:
    try:
        request, execution = service.approve_approval(
            approval_id,
            step_indexes=payload.step_indexes,
            execute_after=payload.execute_after,
            dry_run=payload.dry_run,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))

    response = {
        "approval": dataclass_to_dict(request),
        "execution": dataclass_to_dict(execution) if execution is not None else None,
    }
    return JSONResponse(response)


@app.post("/api/approvals/{approval_id}/deny")
def deny_approval(approval_id: str, payload: ApprovalDenyRequest) -> JSONResponse:
    try:
        request = service.deny_approval(approval_id, reason=payload.reason)
    except KeyError:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    return JSONResponse({"approval": dataclass_to_dict(request)})
