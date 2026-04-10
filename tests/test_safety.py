from app.core.safety import assess_safety


def test_safety_blocks_recursive_delete():
    report = assess_safety(["Remove-Item -Path C:\\Windows -Recurse"])
    assert report.blocked is True


def test_safety_requires_confirmation_for_delete():
    report = assess_safety(['Remove-Item -Path "*.txt"'])
    assert report.blocked is False
    assert report.requires_confirmation is True
