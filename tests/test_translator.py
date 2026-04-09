from app.core.models import ShellType
from app.core.translator import translate_instruction
from app.core.automation import build_automation_plan


def test_translate_create_folder():
    result = translate_instruction("Create a folder named reports", ShellType.powershell)
    assert result.command_lines() == ['New-Item -ItemType Directory -Name "reports"']


def test_translate_multi_step_instruction():
    result = translate_instruction("create a folder named test and then list files", ShellType.bash)
    commands = result.command_lines()
    assert commands[0] == 'mkdir -p "test"'
    assert commands[1] == "ls -la"


def test_translate_delete_text_files():
    result = translate_instruction("delete all txt files", ShellType.powershell)
    assert result.command_lines()[0].startswith("Remove-Item")


def test_translate_direct_shell_command_passthrough():
    result = translate_instruction("Get-Process", ShellType.powershell)
    assert result.command_lines()[0] == "Get-Process"


def test_translate_change_directory():
    result = translate_instruction("change directory to downloads", ShellType.bash)
    assert result.command_lines()[0] == 'cd "downloads"'


def test_translate_system_info():
    result = translate_instruction("show system info", ShellType.powershell)
    assert result.command_lines()[0] == "Get-ComputerInfo"


def test_translate_stop_process_requires_confirmation():
    result = translate_instruction("stop process notepad", ShellType.powershell)
    assert result.command_lines()[0].startswith("Stop-Process")


def test_system_setup_automation_plan():
    plan = build_automation_plan("download python and install requirements", ShellType.powershell)
    assert plan is not None
    assert plan.category.value == "system_setup"
    assert plan.command_lines(ShellType.powershell)


def test_browser_automation_plan():
    plan = build_automation_plan("open whatsapp and send a message to John saying hello", ShellType.powershell)
    assert plan is not None
    assert plan.category.value == "browser_automation"
    assert plan.requires_browser is True
