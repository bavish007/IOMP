from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
AUDIT_FILE = DATA_DIR / "audit_log.jsonl"


@dataclass(slots=True)
class AuditEvent:
    event_type: str
    timestamp: str
    payload: dict[str, Any]


def _ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not AUDIT_FILE.exists():
        AUDIT_FILE.write_text("", encoding="utf-8")


def record_event(event_type: str, payload: dict[str, Any]) -> None:
    _ensure_store()
    event = AuditEvent(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload=payload,
    )
    with AUDIT_FILE.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


def list_events(limit: int = 100) -> list[AuditEvent]:
    _ensure_store()
    events: list[AuditEvent] = []
    for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines()[-limit:]:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            events.append(
                AuditEvent(
                    event_type=str(data.get("event_type", "unknown")),
                    timestamp=str(data.get("timestamp", "")),
                    payload=dict(data.get("payload", {})),
                )
            )
        except Exception:
            continue
    return events
