from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import reading_spelling_coach as coach


def test_save_score_writes_activity_label(monkeypatch, tmp_path):
    score_file = tmp_path / "score_history.txt"
    monkeypatch.setattr(coach, "SCORE_HISTORY_FILE", str(score_file))

    coach.save_score(1, 1, activity="Spelling Test")
    coach.save_score(0, 1, activity="Random Practice")

    lines = score_file.read_text().splitlines()
    assert " | Spelling Test | Score: 1 out of 1" in lines[0]
    assert " | Random Practice | Score: 0 out of 1" in lines[1]


def test_parse_score_history_supports_old_new_and_mixed_records(tmp_path):
    score_file = tmp_path / "score_history.txt"
    score_file.write_text(
        "2026-07-15 11:40 PM | Score: 2 out of 3\n"
        "2026-07-15 11:43 PM | Spelling Test | Score: 1 out of 1\n"
        "2026-07-15 11:44 PM | Random Practice | Score: 0 out of 1\n"
        "bad line\n"
    )

    records = coach.load_score_records(str(score_file))

    assert [record.activity for record in records] == [None, "Spelling Test", "Random Practice"]
    assert [(record.score, record.total) for record in records] == [(2, 3), (1, 1), (0, 1)]
    assert coach.calculate_score_percentages(records) == [66.66666666666666, 100.0, 0.0]


def test_progress_report_does_not_crash_on_mixed_score_records(monkeypatch, tmp_path, capsys):
    words = tmp_path / "words.txt"
    meanings = tmp_path / "meanings.txt"
    pending = tmp_path / "pending_words.txt"
    missed = tmp_path / "missed_words.txt"
    scores = tmp_path / "score_history.txt"
    words.write_text("router\n")
    meanings.write_text("router|A network device.\n")
    pending.write_text("")
    missed.write_text("")
    scores.write_text(
        "2026-07-15 11:40 PM | Score: 2 out of 3\n"
        "2026-07-15 11:43 PM | Spelling Test | Score: 1 out of 1\n"
    )
    monkeypatch.setattr(coach, "WORDS_FILE", str(words))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending))
    monkeypatch.setattr(coach, "MISSED_WORDS_FILE", str(missed))
    monkeypatch.setattr(coach, "SCORE_HISTORY_FILE", str(scores))

    coach.show_progress_report()
    output = capsys.readouterr().out

    assert "Saved score records: 2" in output
    assert "Average score percent" in output
