from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from reading_spelling_coach import is_exit_choice


def test_exit_words_are_exit_choices():
    exit_words = ["q", "quit", "menu", " Q ", "MENU"]

    for user_text in exit_words:
        assert is_exit_choice(user_text) is True


def test_other_words_are_not_exit_choices():
    other_words = ["1", "practice", "", "qu", "main menu"]

    for user_text in other_words:
        assert is_exit_choice(user_text) is False
