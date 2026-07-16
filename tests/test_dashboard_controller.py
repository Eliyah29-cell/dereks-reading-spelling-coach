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


def test_feedback_view_state_survives_display_setting_changes_and_keeps_final_score():
    controller = logic.DashboardController()
    activity = logic.RandomPracticeSession(
        words=["router"],
        meanings={},
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    prompt = activity.start()
    controller.add_prompt_to_history(activity.activity_label, prompt)
    feedback = activity.submit_answer("router")
    controller.add_feedback_to_history(activity.activity_label, feedback, "router")

    for setting_update in [
        {"font_size": 24},
        {"spacing": 20},
        {"high_contrast": True},
    ]:
        controller.update_display_settings(**setting_update)
        assert controller.current_screen == "feedback"
        assert controller.current_feedback.message == "Correct! Great job."
        assert controller.current_feedback.final_score == 1
        assert controller.current_feedback.final_total == 1
        assert activity.current_word is None
        assert activity.finished is True


def test_activity_history_retains_questions_feedback_and_hides_spelling_prompt_word():
    controller = logic.DashboardController()
    random_activity = logic.RandomPracticeSession(
        words=["router"],
        meanings={"router": "A network device."},
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    random_prompt = random_activity.start()
    controller.add_prompt_to_history(random_activity.activity_label, random_prompt)
    random_feedback = random_activity.submit_answer("wrong")
    controller.add_feedback_to_history(random_activity.activity_label, random_feedback, "wrong")

    spelling_activity = logic.SpellingTestSession(
        words=["secret"],
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    spelling_prompt = spelling_activity.start()
    controller.add_prompt_to_history(spelling_activity.activity_label, spelling_prompt)

    assert controller.activity_history[0].visible_word == "router"
    assert controller.activity_history[0].meaning == "A network device."
    assert controller.activity_history[1].submitted_answer == "wrong"
    assert controller.activity_history[1].revealed_word == "router"
    assert controller.activity_history[2].activity_label == "Spelling Test"
    assert controller.activity_history[2].visible_word is None
    assert "secret" not in str(controller.activity_history[2])


def test_scrollbar_drag_upward_pauses_and_jump_resumes_auto_scroll_state():
    state = logic.AutoScrollState()
    state.add_active_output()
    state.mark_scrolled_to_active()

    state.manual_scroll_up()
    assert state.auto_scroll_paused is True
    assert state.should_show_jump_control is True
    assert state.scroll_to_active_requested is False

    state.jump_to_current_question()
    assert state.auto_scroll_paused is False
    assert state.should_show_jump_control is False
    assert state.scroll_to_active_requested is True


def test_new_activity_and_home_reset_auto_scroll_state():
    state = logic.AutoScrollState()
    state.manual_scroll_up()
    assert state.auto_scroll_paused is True

    state.reset_for_new_activity()
    assert state.auto_scroll_paused is False
    assert state.should_show_jump_control is False
    assert state.scroll_to_active_requested is False


def test_home_page_scroll_does_not_pause_new_activity_auto_scroll():
    state = logic.AutoScrollState()
    # Home-page scrolling is intentionally not represented as an activity manual_scroll_up call.
    assert state.auto_scroll_paused is False
    state.reset_for_new_activity()
    assert state.add_active_output() is True


def test_prepare_spelling_test_words_shuffles_copy_without_modifying_original():
    original_words = ["router", "firewall", "malware"]

    def fake_shuffle(words):
        words[:] = ["malware", "router", "firewall"]

    shuffled = logic.prepare_spelling_test_words(original_words, shuffle_words=fake_shuffle)

    assert shuffled == ["malware", "router", "firewall"]
    assert original_words == ["router", "firewall", "malware"]
    assert sorted(shuffled) == sorted(original_words)


def test_random_practice_amount_validation_rejects_invalid_values_and_accepts_bounds():
    invalid_values = ["", "abc", "0", "-1", "4"]

    for value in invalid_values:
        valid, amount, message = logic.validate_random_practice_amount(value, 3)
        assert valid is False
        assert amount is None
        assert message == "Choose a number from 1 through 3."

    assert logic.validate_random_practice_amount("1", 3) == (True, 1, "")
    assert logic.validate_random_practice_amount("3", 3) == (True, 3, "")


def test_random_practice_back_path_returns_to_home_without_stale_state():
    controller = logic.DashboardController()
    controller.push_screen("random_menu")
    controller.replace_screen("random_menu")
    controller.push_screen("random_amount")

    assert controller.back() == "random_menu"
    assert controller.back() == "home"


def test_auto_scroll_event_controller_pauses_only_activity_upward_scrolls():
    state = logic.AutoScrollState()
    events = logic.AutoScrollEventController(state)

    events.mouse_wheel(delta=120, in_activity=False)
    assert state.auto_scroll_paused is False

    events.mouse_wheel(delta=120, in_activity=True)
    assert state.auto_scroll_paused is True
    assert state.should_show_jump_control is True

    state.reset_for_new_activity()
    events.linux_button_4(in_activity=True)
    assert state.auto_scroll_paused is True

    state.reset_for_new_activity()
    events.keyboard_scroll("Prior", in_activity=True)
    assert state.auto_scroll_paused is True

    state.reset_for_new_activity()
    events.keyboard_scroll("Next", in_activity=True)
    assert state.auto_scroll_paused is False


def test_auto_scroll_event_controller_scrollbar_drag_up_pauses_and_down_does_not():
    state = logic.AutoScrollState()
    events = logic.AutoScrollEventController(state)

    events.scrollbar_drag(previous_fraction=0.2, current_fraction=0.4, in_activity=True)
    assert state.auto_scroll_paused is False

    events.scrollbar_drag(previous_fraction=0.4, current_fraction=0.2, in_activity=True)
    assert state.auto_scroll_paused is True
    assert state.should_show_jump_control is True

    events.jump_to_current_question()
    assert state.auto_scroll_paused is False
    assert state.scroll_to_active_requested is True


def test_actual_random_practice_back_button_path_returns_home_next():
    controller = logic.DashboardController()
    controller.open_activity("random_practice")
    controller.push_screen("random_menu")
    controller.replace_screen("random_menu")
    controller.push_screen("random_amount")

    controller.back_to_random_choices_from_amount()

    assert controller.current_screen == "random_menu"
    assert controller.back_stack == []
    assert controller.back() == "home"


def test_showing_jump_control_does_not_require_history_rebuild():
    controller = logic.DashboardController()
    state = logic.AutoScrollState()
    prompt = logic.ActivityPrompt("router", "A device.", True, "Type the word.", 1, 1)
    controller.add_prompt_to_history("Random Practice", prompt)
    original_history = list(controller.activity_history)

    state.manual_scroll_up()

    assert state.should_show_jump_control is True
    assert controller.activity_history == original_history


def test_downward_scroll_to_bottom_resumes_auto_scroll_and_hides_jump_state():
    state = logic.AutoScrollState()
    events = logic.AutoScrollEventController(state)
    state.manual_scroll_up()
    assert state.should_show_jump_control is True

    events.downward_scroll_finished_at_bottom(at_bottom=True)

    assert state.auto_scroll_paused is False
    assert state.should_show_jump_control is False
    assert state.scroll_to_active_requested is False


def test_downward_scroll_not_at_bottom_keeps_auto_scroll_paused():
    state = logic.AutoScrollState()
    events = logic.AutoScrollEventController(state)
    state.manual_scroll_up()

    events.downward_scroll_finished_at_bottom(at_bottom=False)

    assert state.auto_scroll_paused is True
    assert state.should_show_jump_control is True
