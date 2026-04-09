from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from .models import ShellType


@dataclass(slots=True)
class AITranslation:
    commands: list[str]
    description: str
    confidence: float
    notes: list[str]


def ai_is_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def translate_with_ai(instruction: str, shell: ShellType) -> AITranslation | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except Exception:
        return None

    client = OpenAI(api_key=api_key)
    prompt = (
        "You are a command translation engine. Convert the user instruction into shell commands. "
        "Return JSON with keys: description, commands, confidence, notes. "
        "Commands must be a list of strings for the requested shell only. "
        f"Requested shell: {shell.value}. "
        "Keep commands short, safe, and concrete."
    )
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": instruction},
        ],
        temperature=0.1,
    )

    raw_text = getattr(response, "output_text", "") or ""
    if not raw_text:
        return None

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, re.S)
    if fenced_match:
        raw_text = fenced_match.group(1)
    else:
        inline_match = re.search(r"(\{.*\})", raw_text, re.S)
        if inline_match:
            raw_text = inline_match.group(1)

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None

    commands = payload.get("commands") or []
    if not isinstance(commands, list):
        return None

    return AITranslation(
        description=str(payload.get("description", "AI-generated command plan")),
        commands=[str(command) for command in commands if str(command).strip()],
        confidence=float(payload.get("confidence", 0.8)),
        notes=[str(note) for note in payload.get("notes", []) if str(note).strip()],
    )
