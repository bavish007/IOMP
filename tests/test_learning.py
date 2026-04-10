from app.core.learning import find_best_match, record_success
from app.core.models import ShellType


def test_learning_record_and_match():
    instruction = "list all active processes"
    commands = ["Get-Process"]
    record_success(instruction=instruction, shell=ShellType.powershell, commands=commands)

    matched = find_best_match("show active processes", shell=ShellType.powershell, min_score=0.1)
    assert matched is not None
    assert matched.commands == commands
