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
    chat_response: str


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

    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = (
        "You are an expert developer AI assistant executing through a shell. "
        "Convert the user's natural language request into the exact shell commands needed to fulfill it. "
        "IMPORTANT: When the user asks you to write content, fill a file with characters, generate code, or scaffold, "
        "you MUST write the actual code required to generate and insert that content into the file. Do not simply touch or create an empty placeholder file. "
        "IMPORTANT: When generating commands that install packages, download files, or update systems (e.g. winget, pip, npm, apt), you MUST strictly use flags to force completely silent, non-interactive execution (e.g., `--silent`, `--quiet`, `--accept-source-agreements`, `--accept-package-agreements`, `-y`). If a command requires user input to proceed, the system will hang infinitely because there is no human attached to the invisible execution pipeline.\n"
        "IMPORTANT: If the user asks about the 'latest version' of a software, do NOT write a script to curl/scrape the software's website. Instead, you must immediately generate the package manager command to autonomously install or update that specific software on their machine.\n"
        "IMPORTANT: If the user is just asking a conversational question, answering a question, or otherwise explicitly NOT asking you to modify the system or retrieve terminal data, leave the `commands` list completely EMPTY ([]). You are a conversational assistant first and foremost. Only execute scripts when the user intends for you to take system actions.\n"
        "IMPORTANT: If the user explicitly instructs you to launch a website, search the web, open a GUI program, or open a file explorer folder, you MUST generate the exact native shell command to physically launch that graphical window on their screen (e.g., `Start-Process 'https://google.com/search?q=query'` or `explorer.exe 'C:\\path'` in PowerShell, or `xdg-open` in Bash).\n"
        "Use here-strings (e.g. @'\n...\n'@ | Out-File -Encoding utf8) in PowerShell or `cat << 'EOF' > ...` in Bash to physically write data to files. "
        f"Requested target shell: {shell.value}. "
        "Return the response strictly as valid JSON with the following keys:\n"
        "- 'chat_response': A natural, conversational, professional AI assistant (JARVIS-like) response speaking directly to the user (e.g. 'Right away, sir. I am installing Python directly into your system.').\n"
        "- 'description': single summary string\n"
        "- 'commands': a list of strings, where each string is a fully formed, valid shell command\n"
        "- 'confidence': a float between 0.0 and 1.0\n"
        "- 'notes': a list of strings for context\n"
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": instruction},
            ],
            temperature=0.1,
            timeout=25.0,
        )
        raw_text = response.choices[0].message.content or ""
    except Exception as e:
        print(f"\n[bold red]FATAL AI ENGINE EXCEPTION:[/bold red] {e}")
        return None
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
        return AITranslation(
            description="Conversational fallback",
            commands=[],
            confidence=0.9,
            notes=[],
            chat_response=raw_text.strip(),
        )

    commands = payload.get("commands") or []
    if not isinstance(commands, list):
        return None

    return AITranslation(
        description=str(payload.get("description", "AI-generated command plan")),
        commands=[str(command) for command in commands if str(command).strip()],
        confidence=float(payload.get("confidence", 0.8)),
        notes=[str(note) for note in payload.get("notes", []) if str(note).strip()],
        chat_response=str(payload.get("chat_response", "Yes, sir. I am executing the requested protocol immediately.")),
    )
