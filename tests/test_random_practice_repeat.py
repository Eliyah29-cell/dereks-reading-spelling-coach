from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import reading_spelling_coach as coach


def redirect_files(monkeypatch, tmp_path):
    meanings = tmp_path / "meanings.txt"
    missed = tmp_path / "missed_words.txt"
    scores = tmp_path / "score_history.txt"
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings))
    monkeypatch.setattr(coach, "MISSED_WORDS_FILE", str(missed))
    monkeypatch.setattr(coach, "SCORE_HISTORY_FILE", str(scores))
    meanings.write_text(
        "computer|An electronic learning tool.\n"
        "network|Connected computers.\n"
        "phishing|A fake message that tries to steal information.\n"
        "security|Protection from danger.\n"
        "router|A device that forwards network traffic.\n"
    )
    return meanings, missed, scores


def test_main_menu_has_combined_random_practice_and_17_options(capsys):
    coach.show_menu()
    output = capsys.readouterr().out
    numbered = [line for line in output.splitlines() if line[:1].isdigit()]
    assert len(numbered) == 17
    assert "15. Random Practice" in output
    assert "16. Show progress report" in output
    assert "17. Pronounce a word" in output
    assert "Random practice by level" not in output
    assert "18." not in output


def test_main_dispatches_options_16_and_17_and_rejects_18(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(coach, "load_words", lambda: ["router"])
    monkeypatch.setattr(coach, "show_progress_report", lambda: calls.append("progress"))
    monkeypatch.setattr(coach, "pronounce_custom_word", lambda: calls.append("pronounce"))
    answers = iter(["16", "17", "18", "11"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.main()
    assert calls == ["progress", "pronounce"]
    assert "Please choose a valid option: 1 through 17." in capsys.readouterr().out


def test_random_practice_menu_offers_six_choices_and_uses_selected_groups(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(coach, "load_words", lambda: ["all-word"])
    monkeypatch.setattr(coach, "LEVELS", {
        "easy": ["easy-word"], "medium": ["medium-word"],
        "hard": ["hard-word"], "cybersecurity": ["cyber-word"],
    })
    monkeypatch.setattr(coach, "random_word_practice", lambda words: calls.append(list(words)))
    for choice in ["1", "2", "3", "4", "5", "6"]:
        monkeypatch.setattr("builtins.input", lambda prompt="", choice=choice: choice)
        coach.random_practice_menu()
    output = capsys.readouterr().out
    for text in ["1. All words", "2. Easy", "3. Medium", "4. Hard", "5. Cybersecurity", "6. Return to main menu"]:
        assert text in output
    assert calls == [["all-word"], ["easy-word"], ["medium-word"], ["hard-word"], ["cyber-word"]]


def test_random_practice_displays_word_meaning_repeats_and_scores(monkeypatch, tmp_path, capsys):
    _, missed, scores = redirect_files(monkeypatch, tmp_path)
    monkeypatch.setattr(coach.random, "sample", lambda population, amount: [population[0]])
    spoken = []
    monkeypatch.setattr(coach, "pronounce_word", lambda word: spoken.append(word))
    answers = iter(["1", "r", "repeat", "router"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.random_word_practice(["router"])
    output = capsys.readouterr().out
    assert "Word: router" in output
    assert "Meaning: A device that forwards network traffic." in output
    assert spoken == ["router", "router", "router"]
    assert not missed.exists()
    assert "Score: 1 out of 1" in scores.read_text()


def test_random_practice_incorrect_saves_missed_and_quit_is_safe(monkeypatch, tmp_path):
    _, missed, scores = redirect_files(monkeypatch, tmp_path)
    monkeypatch.setattr(coach.random, "sample", lambda population, amount: [population[0]])
    monkeypatch.setattr(coach, "pronounce_word", lambda word: None)
    answers = iter(["1", "wrong"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.random_word_practice(["router"])
    assert missed.read_text() == "router\n"
    assert "Score: 0 out of 1" in scores.read_text()
    answers = iter(["1", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.random_word_practice(["router"])


def test_spelling_test_hides_word_until_incorrect_and_repeat_does_not_count(monkeypatch, tmp_path, capsys):
    _, missed, scores = redirect_files(monkeypatch, tmp_path)
    monkeypatch.setattr(coach.random, "shuffle", lambda words: None)
    spoken = []
    monkeypatch.setattr(coach, "pronounce_word", lambda word: spoken.append(word))
    answers = iter(["r", "repeat", "wrong"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.spelling_test(["router"])
    output = capsys.readouterr().out
    assert "Study this word: router" not in output
    assert output.index("Spelling Test") < output.index("Incorrect. The correct spelling is: router")
    assert spoken == ["router", "router", "router"]
    assert missed.read_text() == "router\n"
    assert "Score: 0 out of 1" in scores.read_text()


def test_spelling_test_correct_and_quit(monkeypatch, tmp_path):
    _, missed, scores = redirect_files(monkeypatch, tmp_path)
    monkeypatch.setattr(coach.random, "shuffle", lambda words: None)
    monkeypatch.setattr(coach, "pronounce_word", lambda word: None)
    answers = iter(["router"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.spelling_test(["router"])
    assert not missed.exists()
    assert "Score: 1 out of 1" in scores.read_text()
    answers = iter(["menu"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    coach.spelling_test(["router"])


def test_pronounce_word_uses_mocked_subprocess_and_current_spd_say_arguments(monkeypatch):
    calls = []
    monkeypatch.setattr(coach.subprocess, "run", lambda args, check=False: calls.append((args, check)))
    coach.pronounce_word(" router ")
    assert calls == [(["spd-say", "-r", "-35", "-p", "5", "router"], False)]
