from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import reading_spelling_coach as coach


def test_approve_pending_words_saves_word_meaning_pairs_and_clears_pending(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"

    words_file.write_text("computer\nrouter\n")
    meanings_file.write_text("computer|An electronic learning tool.\n")
    pending_file.write_text(
        "router|A duplicate should not be added.\n"
        "firewall|A tool that blocks unsafe network traffic.\n"
        "legacyword\n"
    )

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr("builtins.input", lambda prompt="": "yes")

    backup_calls = []
    monkeypatch.setattr(coach, "backup_project_to_8tb", lambda: backup_calls.append("called"))

    coach.approve_pending_words()

    assert words_file.read_text() == "computer\nrouter\nfirewall\nlegacyword\n"
    assert meanings_file.read_text() == (
        "computer|An electronic learning tool.\n"
        "firewall|A tool that blocks unsafe network traffic.\n"
        "legacyword|No meaning found yet.\n"
    )
    assert pending_file.read_text() == ""
    assert backup_calls == ["called"]


def test_reject_pending_words_leaves_temporary_files_unchanged_and_skips_backup(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"

    words_file.write_text("computer\n")
    meanings_file.write_text("computer|An electronic learning tool.\n")
    pending_text = "router|A device that forwards network traffic.\n"
    pending_file.write_text(pending_text)

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr("builtins.input", lambda prompt="": "no")

    backup_calls = []
    monkeypatch.setattr(coach, "backup_project_to_8tb", lambda: backup_calls.append("called"))

    coach.approve_pending_words()

    assert words_file.read_text() == "computer\n"
    assert meanings_file.read_text() == "computer|An electronic learning tool.\n"
    assert pending_file.read_text() == pending_text
    assert backup_calls == []


def test_random_word_practice_pronounces_hidden_word_before_answer(monkeypatch, tmp_path, capsys):
    meanings_file = tmp_path / "meanings.txt"
    missed_file = tmp_path / "missed_words.txt"
    score_file = tmp_path / "score_history.txt"
    meanings_file.write_text("router|A device that forwards network traffic.\n")

    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "MISSED_WORDS_FILE", str(missed_file))
    monkeypatch.setattr(coach, "SCORE_HISTORY_FILE", str(score_file))
    monkeypatch.setattr(coach.random, "sample", lambda population, amount: [population[0]])

    spoken_words = []
    monkeypatch.setattr(coach, "pronounce_word", lambda word: spoken_words.append(word))

    answers = iter(["1", "router"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    coach.random_word_practice(["router"])

    output = capsys.readouterr().out

    assert spoken_words == ["router"]
    assert "Meaning: A device that forwards network traffic." in output
    assert "Meaning: router|" not in output
    assert not missed_file.exists()
    assert "Score: 1 out of 1" in score_file.read_text()


def test_random_practice_by_level_pronounces_hidden_word_before_answer(monkeypatch, tmp_path):
    meanings_file = tmp_path / "meanings.txt"
    missed_file = tmp_path / "missed_words.txt"
    score_file = tmp_path / "score_history.txt"
    meanings_file.write_text("router|A device that forwards network traffic.\n")

    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "MISSED_WORDS_FILE", str(missed_file))
    monkeypatch.setattr(coach, "SCORE_HISTORY_FILE", str(score_file))
    monkeypatch.setattr(coach, "LEVELS", {"easy": ["router"], "medium": [], "hard": [], "cybersecurity": []})
    monkeypatch.setattr(coach.random, "sample", lambda population, amount: [population[0]])

    spoken_words = []
    monkeypatch.setattr(coach, "pronounce_word", lambda word: spoken_words.append(word))

    answers = iter(["2", "1", "wrong"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    coach.random_practice_menu()

    assert spoken_words == ["router"]
    assert missed_file.read_text() == "router\n"
    assert "Score: 0 out of 1" in score_file.read_text()
