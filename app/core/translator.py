from __future__ import annotations

import os
import re

from .ai import ai_is_available, translate_with_ai
from .models import CommandAction, ShellType, TranslationResult


def _normalize(text: str) -> str:
    compact = re.sub(r"\s+", " ", text.strip().lower())
    return compact


def _split_intents(text: str) -> list[str]:
    fragments = [
        fragment.strip()
        for fragment in re.split(
            r"\b(?:and then|then)\b|;|\n|\band\b(?=\s+(?:create|make|new|delete|remove|erase|list|show|display|move|rename|copy|duplicate|print|echo)\b)",
            text,
        )
        if fragment.strip()
    ]
    if fragments:
        return fragments
    return [text.strip()]


def _folder_name(fragment: str) -> str:
    match = re.search(r"(?:named|called)\s+([\w\-\. ]+)$", fragment)
    if match:
        return re.sub(r"\b(?:and|then)\b.*$", "", match.group(1)).strip()
    match = re.search(r"(?:folder|directory)\s+([\w\-\. ]+)$", fragment)
    if match:
        return re.sub(r"\b(?:and|then)\b.*$", "", match.group(1)).strip()
    return "new-folder"


def _file_name(fragment: str) -> str:
    match = re.search(r"(?:named|called)\s+([\w\-\.]+(?:\.[\w\-]+)?)$", fragment)
    if match:
        return re.sub(r"\b(?:and|then)\b.*$", "", match.group(1)).strip()
    match = re.search(r"file\s+([\w\-\.]+(?:\.[\w\-]+)?)$", fragment)
    if match:
        return re.sub(r"\b(?:and|then)\b.*$", "", match.group(1)).strip()
    return "new-file.txt"


def _target_path(fragment: str) -> str:
    match = re.search(r"(?:to|into|in)\s+([\w\-\\/\. ]+)$", fragment)
    if match:
        return re.sub(r"\b(?:and|then)\b.*$", "", match.group(1)).strip()
    return "destination-folder"


def _looks_like_shell_command(text: str) -> bool:
    shell_markers = [
        r"\b(New-Item|Get-Process|Get-ChildItem|Remove-Item|Move-Item|Copy-Item|Rename-Item|Write-Output)\b",
        r"\b(mkdir|ls|cp|mv|rm|pwd|echo|touch)\b",
        r"^\s*\./",
        r"^\s*[A-Za-z]:\\",
    ]
    return any(re.search(marker, text, re.I) for marker in shell_markers)


def _commands_for_create_folder(fragment: str) -> CommandAction:
    name = _folder_name(fragment)
    return CommandAction(
        description=f"Create folder {name}",
        commands={
            ShellType.powershell: f"New-Item -ItemType Directory -Name \"{name}\"",
            ShellType.bash: f'mkdir -p "{name}"',
        },
    )


def _commands_for_create_file(fragment: str) -> CommandAction:
    name = _file_name(fragment)
    return CommandAction(
        description=f"Create file {name}",
        commands={
            ShellType.powershell: f'New-Item -ItemType File -Name "{name}"',
            ShellType.bash: f'touch "{name}"',
        },
    )


def _commands_for_list_processes() -> CommandAction:
    return CommandAction(
        description="List running processes",
        commands={
            ShellType.powershell: "Get-Process",
            ShellType.bash: "ps -eo pid,ppid,cmd --sort=pid",
        },
    )


def _commands_for_list_directory() -> CommandAction:
    return CommandAction(
        description="List files in the current directory",
        commands={
            ShellType.powershell: "Get-ChildItem",
            ShellType.bash: "ls -la",
        },
    )


def _commands_for_print_working_directory() -> CommandAction:
    return CommandAction(
        description="Show current directory",
        commands={
            ShellType.powershell: "Get-Location",
            ShellType.bash: "pwd",
        },
    )


def _commands_for_system_info() -> CommandAction:
    return CommandAction(
        description="Show system information",
        commands={
            ShellType.powershell: "Get-ComputerInfo",
            ShellType.bash: "uname -a && (lsb_release -a 2>/dev/null || cat /etc/os-release)",
        },
    )


def _commands_for_ip_info() -> CommandAction:
    return CommandAction(
        description="Show IP configuration",
        commands={
            ShellType.powershell: "ipconfig",
            ShellType.bash: "ip addr || ifconfig",
        },
    )


def _commands_for_disk_usage() -> CommandAction:
    return CommandAction(
        description="Show disk usage",
        commands={
            ShellType.powershell: "Get-PSDrive -PSProvider FileSystem",
            ShellType.bash: "df -h",
        },
    )


def _commands_for_change_directory(fragment: str) -> CommandAction:
    target = _target_path(fragment)
    return CommandAction(
        description=f"Change directory to {target}",
        commands={
            ShellType.powershell: f'Set-Location "{target}"',
            ShellType.bash: f'cd "{target}"',
        },
    )


def _commands_for_find_file(fragment: str) -> CommandAction:
    name = _file_name(fragment)
    return CommandAction(
        description=f"Find file {name}",
        commands={
            ShellType.powershell: f'Get-ChildItem -Path . -Recurse -Filter "{name}" | Select-Object -ExpandProperty FullName',
            ShellType.bash: f'find . -name "{name}"',
        },
    )


def _commands_for_search_text(fragment: str) -> CommandAction:
    match = re.search(r"(?:search for|find|grep for)\s+(.+?)\s+(?:in|inside|within)\s+([\w\-\/\\\. ]+)$", fragment)
    pattern = match.group(1).strip() if match else "pattern"
    target = match.group(2).strip() if match else "."
    return CommandAction(
        description=f"Search for {pattern} in {target}",
        commands={
            ShellType.powershell: f'Select-String -Path "{target}" -Pattern "{pattern}" -Recurse',
            ShellType.bash: f'grep -RIn "{pattern}" "{target}"',
        },
    )


def _commands_for_stop_process(fragment: str) -> CommandAction:
    match = re.search(r"(?:stop|kill|end)\s+(?:process\s+)?([\w\-\.]+)$", fragment)
    name = match.group(1).strip() if match else "process-name"
    return CommandAction(
        description=f"Stop process {name}",
        commands={
            ShellType.powershell: f'Stop-Process -Name "{name}" -Force',
            ShellType.bash: f'pkill -f "{name}"',
        },
        risk_tags=["process-termination"],
    )


def _commands_for_delete_txt(fragment: str) -> CommandAction:
    pattern = fragment
    if ".txt" not in pattern:
        pattern = "*.txt"
    return CommandAction(
        description="Delete text files",
        commands={
            ShellType.powershell: f'Remove-Item -Path "{pattern}"',
            ShellType.bash: f'rm -f {pattern}',
        },
        risk_tags=["file-delete"],
    )


def _commands_for_move_files(fragment: str) -> CommandAction:
    destination = _target_path(fragment)
    source = "*.txt"
    return CommandAction(
        description=f"Move files to {destination}",
        commands={
            ShellType.powershell: f'Move-Item -Path "{source}" -Destination "{destination}"',
            ShellType.bash: f'mv {source} "{destination}"',
        },
    )


def _commands_for_rename_file(fragment: str) -> CommandAction:
    match = re.search(r"rename\s+([\w\-\.]+(?:\.[\w\-]+)?)\s+to\s+([\w\-\.]+(?:\.[\w\-]+)?)", fragment)
    if match:
        source, destination = match.groups()
    else:
        source, destination = "source.txt", "destination.txt"
    return CommandAction(
        description=f"Rename {source} to {destination}",
        commands={
            ShellType.powershell: f'Rename-Item -Path "{source}" -NewName "{destination}"',
            ShellType.bash: f'mv "{source}" "{destination}"',
        },
    )


def _commands_for_copy_file(fragment: str) -> CommandAction:
    destination = _target_path(fragment)
    source = "source.txt"
    return CommandAction(
        description=f"Copy file to {destination}",
        commands={
            ShellType.powershell: f'Copy-Item -Path "{source}" -Destination "{destination}"',
            ShellType.bash: f'cp "{source}" "{destination}"',
        },
    )


def _commands_for_echo(fragment: str) -> CommandAction:
    message = fragment.split("echo", 1)[-1].strip() or "Hello from Talk2Shell"
    return CommandAction(
        description="Print text to the terminal",
        commands={
            ShellType.powershell: f'Write-Output "{message}"',
            ShellType.bash: f'echo "{message}"',
        },
    )


def translate_instruction(instruction: str, shell: ShellType) -> TranslationResult:
    normalized = _normalize(instruction)

    if _looks_like_shell_command(normalized):
        return TranslationResult(
            original_text=instruction,
            normalized_text=normalized,
            shell=shell,
            actions=[
                CommandAction(
                    description="Direct shell command",
                    commands={
                        ShellType.powershell: instruction,
                        ShellType.bash: instruction,
                    },
                )
            ],
            confidence=0.93,
            notes=["Detected a shell command and passed it through directly."],
        )

    if ai_is_available():
        ai_translation = translate_with_ai(instruction, shell)
<<<<<<< HEAD
        if ai_translation:
=======
        if ai_translation and ai_translation.commands:
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07
            actions = [
                CommandAction(
                    description=f"{ai_translation.description} {index + 1}" if len(ai_translation.commands) > 1 else ai_translation.description,
                    commands={current_shell: command for current_shell in ShellType},
                )
                for index, command in enumerate(ai_translation.commands)
            ]
            return TranslationResult(
                original_text=instruction,
                normalized_text=normalized,
                shell=shell,
                actions=actions,
                confidence=ai_translation.confidence,
                notes=ai_translation.notes,
<<<<<<< HEAD
                chat_response=ai_translation.chat_response,
=======
>>>>>>> 05faf86e9b6137bc9bb72f8fb0ca83492ec97c07
            )

    fragments = _split_intents(normalized)
    actions: list[CommandAction] = []
    notes: list[str] = []

    for fragment in fragments:
        if re.search(r"\b(create|make|new)\b.*\b(folder|directory)\b", fragment):
            actions.append(_commands_for_create_folder(fragment))
        elif re.search(r"\b(create|make|new)\b.*\b(file)\b", fragment):
            actions.append(_commands_for_create_file(fragment))
        elif re.search(r"\b(open|show|display)\b.*\b(system info|computer info|device info)\b", fragment):
            actions.append(_commands_for_system_info())
        elif re.search(r"\b(show|display|what is)\b.*\b(ip|network)\b", fragment):
            actions.append(_commands_for_ip_info())
        elif re.search(r"\b(show|display)\b.*\b(disk usage|drives|storage)\b", fragment):
            actions.append(_commands_for_disk_usage())
        elif re.search(r"\b(delete|remove|erase)\b.*\b(txt|text)\b", fragment):
            actions.append(_commands_for_delete_txt(fragment))
        elif re.search(r"\b(list|show|display)\b.*\b(process|processes)\b", fragment):
            actions.append(_commands_for_list_processes())
        elif re.search(r"\b(list|show|display)\b.*\b(files|folder|directory|contents)\b", fragment):
            actions.append(_commands_for_list_directory())
        elif re.search(r"\b(show|print|where am i|current directory)\b", fragment):
            actions.append(_commands_for_print_working_directory())
        elif re.search(r"\b(change directory|cd to|go to)\b", fragment):
            actions.append(_commands_for_change_directory(fragment))
        elif re.search(r"\b(find file|locate file|search file)\b", fragment):
            actions.append(_commands_for_find_file(fragment))
        elif re.search(r"\b(search for|find|grep for)\b.*\b(in|inside|within)\b", fragment):
            actions.append(_commands_for_search_text(fragment))
        elif re.search(r"\b(move)\b.*\b(files?|items?)\b", fragment):
            actions.append(_commands_for_move_files(fragment))
        elif re.search(r"\b(rename)\b.*\b(to)\b", fragment):
            actions.append(_commands_for_rename_file(fragment))
        elif re.search(r"\b(copy|duplicate)\b.*\b(file|files|item|items)\b", fragment):
            actions.append(_commands_for_copy_file(fragment))
        elif re.search(r"\b(stop|kill|end)\b.*\b(process|processes|task)\b", fragment):
            actions.append(_commands_for_stop_process(fragment))
        elif fragment.startswith("echo ") or fragment.startswith("print "):
            actions.append(_commands_for_echo(fragment))
        else:
            notes.append(f'Could not translate fragment: "{fragment}"')

    if not actions:
        actions.append(
            CommandAction(
                description="No direct translation available",
                commands={
                    ShellType.powershell: f'Write-Output "No rule matched: {normalized}"',
                    ShellType.bash: f'echo "No rule matched: {normalized}"',
                },
            )
        )

    confidence = 0.92 if not notes else max(0.35, 0.92 - (0.15 * len(notes)))
    return TranslationResult(
        original_text=instruction,
        normalized_text=normalized,
        shell=shell,
        actions=actions,
        confidence=confidence,
        notes=notes,
    )
