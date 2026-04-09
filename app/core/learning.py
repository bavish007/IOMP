from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

from .models import ShellType


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
LEARNING_FILE = DATA_DIR / "learned_commands.json"


@dataclass(slots=True)
class LearnedCommand:
    instruction: str
    normalized_instruction: str
    shell: ShellType
    commands: list[str]
    success_count: int = 1


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_\-]+", _normalize(text)) if len(token) > 1}


def _ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LEARNING_FILE.exists():
        LEARNING_FILE.write_text("[]\n", encoding="utf-8")


def _load_all() -> list[LearnedCommand]:
    _ensure_store()
    raw = json.loads(LEARNING_FILE.read_text(encoding="utf-8"))
    entries: list[LearnedCommand] = []
    for item in raw:
        try:
            entries.append(
                LearnedCommand(
                    instruction=str(item["instruction"]),
                    normalized_instruction=str(item["normalized_instruction"]),
                    shell=ShellType(str(item["shell"])),
                    commands=[str(command) for command in item["commands"]],
                    success_count=int(item.get("success_count", 1)),
                )
            )
        except Exception:
            continue
    return entries


def _save_all(items: list[LearnedCommand]) -> None:
    payload = []
    for item in items:
        row = asdict(item)
        row["shell"] = item.shell.value
        payload.append(row)
    LEARNING_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def record_success(instruction: str, shell: ShellType, commands: list[str]) -> None:
    normalized = _normalize(instruction)
    items = _load_all()

    for item in items:
        if item.normalized_instruction == normalized and item.shell == shell and item.commands == commands:
            item.success_count += 1
            _save_all(items)
            return

    items.append(
        LearnedCommand(
            instruction=instruction,
            normalized_instruction=normalized,
            shell=shell,
            commands=commands,
            success_count=1,
        )
    )
    _save_all(items)


def find_best_match(instruction: str, shell: ShellType, min_score: float = 0.55) -> LearnedCommand | None:
    candidates = [item for item in _load_all() if item.shell == shell]
    if not candidates:
        return None

    target_tokens = _tokenize(instruction)
    if not target_tokens:
        return None

    best_item: LearnedCommand | None = None
    best_score = 0.0
    for item in candidates:
        item_tokens = _tokenize(item.normalized_instruction)
        union = target_tokens | item_tokens
        if not union:
            continue
        score = len(target_tokens & item_tokens) / len(union)
        weighted = score + min(item.success_count / 100.0, 0.15)
        if weighted > best_score:
            best_score = weighted
            best_item = item

    if best_item is None or best_score < min_score:
        return None
    return best_item


def list_learned(shell: ShellType | None = None) -> list[LearnedCommand]:
    items = _load_all()
    if shell is None:
        return items
    return [item for item in items if item.shell == shell]
