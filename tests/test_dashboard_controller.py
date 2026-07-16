from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import dashboard.logic as logic


def fake_pronouncer(calls):
    return lambda word: calls.append(word)


def test_home_groups_and_controls_point_to_approved_activities():
    controller = logic.DashboardController()
    home = controller.home_model()

    assert set(home) == {"Practice", "Word Library", "Review and Progress", "Application"}
    assert home["Practice"]["Random Practice"] == "random_practice"
    assert home["Practice"]["Spelling Test"] == "spelling_test"
    assert home["Review and Progress"]["Score History"] == "score_history"
    assert controller.active_activity is None
    controller.open_activity("score_history")
    assert controller.active_activity == "score_history"
    controller.go_home()
    assert controller.active_activity is None
    assert controller.exit_dashboard() == "exit"


def test_random_practice_controller_shows_word_meaning_repeat_and_scores(tmp_path):
    calls = []
    activity = logic.RandomPracticeSession(
        words=["router"],
        meanings={"router": "A network device."},
        save_missed_word=lambda word: (_ for _ in ()).throw(AssertionError("should not save missed")),
        save_score=lambda score, total, activity: calls.append((score, total, activity)),
        pronounce_word=fake_pronouncer(calls),
    )

    prompt = activity.start()
    assert prompt.word_visible is True
    assert prompt.word == "router"
    assert prompt.meaning == "A network device."
    assert calls == ["router"]

    activity.repeat_word()
    assert calls == ["router", "router"]
    assert activity.score == 0
    assert activity.answered_count == 0

    feedback = activity.submit_answer("router")
    assert feedback.correct is True
    assert activity.score == 1
    assert activity.answered_count == 1
    assert calls[-1] == (1, 1, "Random Practice")


def test_random_practice_wrong_answer_preserves_missed_word_storage_rule():
    missed = []
    saved = []
    activity = logic.RandomPracticeSession(
        words=["router"],
        meanings={},
        save_missed_word=missed.append,
        save_score=lambda score, total, activity: saved.append((score, total, activity)),
        pronounce_word=lambda word: None,
    )
    activity.start()
    feedback = activity.submit_answer("wrong")

    assert feedback.correct is False
    assert feedback.revealed_word == "router"
    assert missed == ["router"]
    assert saved == [(0, 1, "Random Practice")]


def test_spelling_test_controller_hides_word_until_wrong_answer_and_repeat_is_safe():
    spoken = []
    missed = []
    saved = []
    activity = logic.SpellingTestSession(
        words=["router"],
        save_missed_word=missed.append,
        save_score=lambda score, total, activity: saved.append((score, total, activity)),
        pronounce_word=fake_pronouncer(spoken),
    )
    prompt = activity.start()

    assert prompt.word_visible is False
    assert prompt.word is None
    assert spoken == ["router"]
    activity.repeat_word()
    assert spoken == ["router", "router"]
    assert activity.answered_count == 0

    feedback = activity.submit_answer("wrong")
    assert feedback.correct is False
    assert feedback.revealed_word == "router"
    assert missed == ["router"]
    assert saved == [(0, 1, "Spelling Test")]


def test_auto_scroll_state_pauses_and_jump_restores_current_prompt():
    state = logic.AutoScrollState()
    assert state.add_active_output() is True
    assert state.should_show_jump_control is False
    state.manual_scroll_up()
    assert state.add_active_output() is False
    assert state.should_show_jump_control is True
    state.jump_to_current_question()
    assert state.should_show_jump_control is False
    assert state.add_active_output() is True
