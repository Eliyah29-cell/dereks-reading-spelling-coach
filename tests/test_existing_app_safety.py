from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import reading_spelling_coach as coach


def test_terminal_app_imports_without_starting_menu():
    assert callable(coach.main)


def test_terminal_menu_still_has_17_options(capsys):
    coach.show_menu()
    output = capsys.readouterr().out
    numbered = [line for line in output.splitlines() if line[:1].isdigit()]
    assert len(numbered) == 17
    assert "17. Pronounce a word" in output
