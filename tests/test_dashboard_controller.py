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


def test_home_model_marks_unfinished_controls_as_not_functional():
    controller = logic.DashboardController()

    assert "Random Practice" in controller.functional_control_labels()
    assert "Spelling Test" in controller.functional_control_labels()
    assert "Practice All Words" in controller.unfinished_control_labels()
    assert controller.is_functional("practice_all_words") is False


def test_back_returns_to_previous_dashboard_screen():
    controller = logic.DashboardController()
    controller.push_screen("random_menu")
    controller.push_screen("random_amount")
    controller.push_screen("activity_prompt")

    assert controller.back() == "random_amount"
    assert controller.back() == "random_menu"
    assert controller.back() == "home"


def test_select_random_words_uses_mocked_random_sample_for_multi_word_sessions():
    calls = []

    def fake_sample(words, amount):
        calls.append((list(words), amount))
        return ["router", "firewall"]

    selected = logic.select_random_words(["router", "firewall", "malware"], 2, random_sample=fake_sample)

    assert selected == ["router", "firewall"]
    assert calls == [(["router", "firewall", "malware"], 2)]


def test_random_practice_multi_word_question_numbers_and_final_score():
    spoken = []
    saved = []
    missed = []
    activity = logic.RandomPracticeSession(
        words=["router", "firewall"],
        meanings={"router": "A network device.", "firewall": "A security tool."},
        save_missed_word=missed.append,
        save_score=lambda score, total, activity: saved.append((score, total, activity)),
        pronounce_word=fake_pronouncer(spoken),
    )

    first_prompt = activity.start()
    assert first_prompt.question_number == 1
    assert first_prompt.total_questions == 2
    assert first_prompt.word == "router"
    first_feedback = activity.submit_answer("router")
    assert first_feedback.finished is False

    second_prompt = activity.start()
    assert second_prompt.question_number == 2
    assert second_prompt.total_questions == 2
    assert second_prompt.word == "firewall"
    second_feedback = activity.submit_answer("wrong")

    assert second_feedback.finished is True
    assert activity.score == 1
    assert activity.answered_count == 2
    assert missed == ["firewall"]
    assert saved == [(1, 2, "Random Practice")]


def test_spelling_test_multi_word_hides_each_word_and_saves_final_score():
    spoken = []
    saved = []
    activity = logic.SpellingTestSession(
        words=["router", "firewall"],
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: saved.append((score, total, activity)),
        pronounce_word=fake_pronouncer(spoken),
    )

    first_prompt = activity.start()
    assert first_prompt.word is None
    assert first_prompt.word_visible is False
    assert first_prompt.question_number == 1
    activity.submit_answer("router")

    second_prompt = activity.start()
    assert second_prompt.word is None
    assert second_prompt.word_visible is False
    assert second_prompt.question_number == 2
    activity.submit_answer("firewall")

    assert spoken == ["router", "firewall"]
    assert saved == [(2, 2, "Spelling Test")]


def test_display_setting_changes_do_not_reset_active_session_state():
    controller = logic.DashboardController()
    activity = logic.RandomPracticeSession(
        words=["router", "firewall"],
        meanings={},
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    activity.start()
    activity.submit_answer("router")

    controller.update_display_settings(font_size=22, spacing=18, high_contrast=True)

    assert activity.current_word == "firewall"
    assert activity.score == 1
    assert activity.answered_count == 1
    assert controller.display_settings.font_size == 22
    assert controller.display_settings.spacing == 18
    assert controller.display_settings.high_contrast is True


def test_auto_scroll_tracks_real_ui_requests_for_pause_and_jump():
    state = logic.AutoScrollState()

    assert state.add_active_output() is True
    assert state.scroll_to_active_requested is True
    state.mark_scrolled_to_active()
    assert state.scroll_to_active_requested is False

    state.manual_scroll_up()
    assert state.add_active_output() is False
    assert state.should_show_jump_control is True
    assert state.scroll_to_active_requested is False

    state.jump_to_current_question()
    assert state.should_show_jump_control is False
    assert state.scroll_to_active_requested is True
