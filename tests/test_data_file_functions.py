from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import reading_spelling_coach as coach


def test_save_words_and_load_words_use_redirected_words_file(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))

    coach.save_words(["security", "Router", "wi-fi"])

    assert words_file.read_text() == "security\nRouter\nwi-fi\n"
    assert coach.load_words() == ["security", "router", "wi-fi"]


def test_load_words_missing_file_creates_and_returns_default_words(monkeypatch, tmp_path):
    words_file = tmp_path / "missing_words.txt"
    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))

    loaded_words = coach.load_words()

    assert loaded_words == [
        "security",
        "computer",
        "network",
        "password",
        "firewall",
        "malware",
        "phishing",
        "software",
        "hardware",
        "internet",
        "router",
    ]
    assert words_file.exists()


def test_load_words_empty_file_creates_and_returns_default_words(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    words_file.write_text("\n   \n")
    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))

    loaded_words = coach.load_words()

    assert loaded_words[0] == "security"
    assert loaded_words[-1] == "router"
    assert words_file.read_text().startswith("security\ncomputer\n")


def test_load_meanings_loads_valid_lines_and_ignores_lines_without_separator(monkeypatch, tmp_path):
    meanings_file = tmp_path / "meanings.txt"
    meanings_file.write_text(
        "Router | A device that forwards traffic.\n"
        "line without separator\n"
        "Firewall| Protects a network.\n"
        "too|many|separators stay in meaning\n"
        "\n"
    )
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))

    assert coach.load_meanings() == {
        "router": "A device that forwards traffic.",
        "firewall": "Protects a network.",
        "too": "many|separators stay in meaning",
    }


def test_load_meanings_missing_file_returns_empty_dictionary(monkeypatch, tmp_path):
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(tmp_path / "missing_meanings.txt"))

    assert coach.load_meanings() == {}


def test_load_word_set_removes_empty_entries_and_returns_first_pipe_field(tmp_path):
    word_set_file = tmp_path / "pending_words.txt"
    word_set_file.write_text(
        " Router | A device.\n"
        "\n"
        "Firewall\n"
        "   \n"
        "router|Duplicate with different case.\n"
    )

    assert coach.load_word_set(str(word_set_file)) == {"router", "firewall"}


def test_load_word_set_missing_file_returns_empty_set(tmp_path):
    assert coach.load_word_set(str(tmp_path / "missing_pending_words.txt")) == set()


def test_load_missed_words_handles_missing_empty_and_populated_files(monkeypatch, tmp_path):
    missed_words_file = tmp_path / "missed_words.txt"
    monkeypatch.setattr(coach, "MISSED_WORDS_FILE", str(missed_words_file))

    assert coach.load_missed_words() == []

    missed_words_file.write_text("\n  \n")
    assert coach.load_missed_words() == []

    missed_words_file.write_text("Router\n FIREWALL \n\nwi-fi\n")
    assert coach.load_missed_words() == ["router", "firewall", "wi-fi"]
