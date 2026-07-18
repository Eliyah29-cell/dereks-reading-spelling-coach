from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import dashboard.app as app_module
import dashboard.logic as logic
import reading_spelling_coach as coach


class FakeVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def make_headless_app():
    app = app_module.DashboardApp.__new__(app_module.DashboardApp)
    app.controller = logic.DashboardController()
    app.auto_scroll = logic.AutoScrollState()
    app.scroll_events = logic.AutoScrollEventController(app.auto_scroll)
    app.font_size = FakeVar(18)
    app.spacing = FakeVar(12)
    app.high_contrast = FakeVar(False)
    app.answer_var = FakeVar("")
    app.amount_var = FakeVar("1")
    app.word_var = FakeVar("")
    app.meaning_var = FakeVar("")
    app.topic_var = FakeVar("")
    app.internet_suggestions = []
    app.internet_selection_vars = []
    app.active_session = None
    app.current_prompt = None
    app.current_view = "home"
    app.random_group_words = []
    app.spelling_test_words = []
    app.rendered = []
    app.main = None
    app.show_lines = lambda title, lines, push=True: app.rendered.append((title, list(lines), push))
    app.show_activity_prompt = lambda prompt, push=True, add_to_history=False: setattr(app, "current_prompt", prompt)
    app.show_home = lambda: setattr(app, "current_view", "home")
    return app


def test_functional_dashboard_workflows_are_enabled():
    controller = logic.DashboardController()

    assert "Practice All Words" in controller.functional_control_labels()
    assert "Practice by Level" in controller.functional_control_labels()
    assert "Practice Missed Words" in controller.functional_control_labels()
    assert "Add a New Word" in controller.functional_control_labels()
    assert "Pronounce a Word" in controller.functional_control_labels()
    assert "Get New Words from the Internet" in controller.functional_control_labels()
    assert "Show Pending Words" in controller.functional_control_labels()
    assert "Approve Pending Words" in controller.functional_control_labels()
    assert "Progress Report" in controller.functional_control_labels()
    assert controller.unfinished_control_labels() == []


def test_spelling_test_amount_handler_supports_all_words(monkeypatch):
    dashboard = make_headless_app()
    dashboard.amount_var.set("all")
    dashboard.spelling_test_words = ["router", "firewall"]
    spoken = []
    saved = []

    monkeypatch.setattr(coach, "pronounce_word", spoken.append)
    monkeypatch.setattr(coach, "save_missed_word", lambda word: None)
    monkeypatch.setattr(coach, "save_score", lambda score, total, activity: saved.append((score, total, activity)))

    dashboard.start_spelling_test_from_amount()

    assert dashboard.active_session.words == ["router", "firewall"]
    assert dashboard.current_prompt.expected_word == "router"
    assert spoken == ["router"]


def test_repeat_during_feedback_repeats_answered_word_not_next_word():
    spoken = []
    session = logic.SpellingTestSession(
        ["router", "firewall"],
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=spoken.append,
    )

    prompt = session.start()
    feedback = session.submit_answer("wrong", expected_word=prompt.expected_word)
    session.repeat_word()

    assert feedback.revealed_word == "router"
    assert spoken == ["router", "router"]
    assert session.current_word == "firewall"


def test_old_prompt_is_not_submitted_against_newer_session_word():
    missed = []
    session = logic.SpellingTestSession(
        ["router", "firewall"],
        save_missed_word=missed.append,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    old_prompt = session.start()
    session.submit_answer("router", expected_word=old_prompt.expected_word)
    session.advance_after_feedback()
    session.start()

    feedback = session.submit_answer("router", expected_word=old_prompt.expected_word)

    assert feedback.correct is False
    assert "old question" in feedback.message
    assert missed == []


def test_add_word_handler_uses_temporary_word_and_meaning_files(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    dashboard = make_headless_app()
    dashboard.word_var.set("Firewall")
    dashboard.meaning_var.set("A tool that blocks unsafe traffic.")

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))

    dashboard.save_new_word()

    assert words_file.read_text() == "router\nfirewall\n"
    assert "firewall|A tool that blocks unsafe traffic." in meanings_file.read_text()
    assert dashboard.rendered[-1][0] == "Add New Word"


def test_approve_selected_pending_words_preserves_unselected_pending(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    pending_file.write_text("firewall|A security barrier.\nmalware|Harmful software.\n")
    dashboard = make_headless_app()
    dashboard.pending_selection_vars = [
        (FakeVar(True), "firewall", "A security barrier."),
        (FakeVar(False), "malware", "Harmful software."),
    ]

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))

    dashboard.approve_selected_pending_words()

    assert words_file.read_text() == "router\nfirewall\n"
    assert "firewall|A security barrier." in meanings_file.read_text()
    assert pending_file.read_text() == "malware|Harmful software.\n"


def test_spacing_change_preserves_active_prompt_and_answer_text():
    dashboard = make_headless_app()
    dashboard.current_view = "activity_prompt"
    dashboard.active_session = logic.PracticeWordsSession(["router"], {}, lambda word: None, lambda score, total, activity: None, lambda word: None)
    prompt = dashboard.active_session.start()
    dashboard.current_prompt = prompt
    dashboard.answer_var.set("rou")
    render_calls = []
    dashboard.render_current_view = lambda: render_calls.append((dashboard.spacing.get(), dashboard.current_prompt, dashboard.answer_var.get()))

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.spacing.get() == 14
    assert render_calls == [(14, prompt, "rou")]


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.payload


class FakeWidget:
    def pack(self, *args, **kwargs):
        return None

    def bind(self, *args, **kwargs):
        return None

    def focus_set(self):
        return None


def make_renderable_headless_app(monkeypatch):
    dashboard = make_headless_app()
    dashboard.clear = lambda: None
    dashboard.heading = lambda parent, text: None
    dashboard.body_text = lambda parent, text: None
    dashboard.make_button = lambda parent, text, command, enabled=True: None
    dashboard.update_jump_control_visibility = lambda: None
    dashboard.render_activity_history = lambda: None
    dashboard.scroll_to_active_if_requested = lambda: None
    dashboard.canvas = type("FakeCanvas", (), {"yview_moveto": lambda self, fraction: None})()
    dashboard.show_activity_prompt = app_module.DashboardApp.show_activity_prompt.__get__(dashboard, app_module.DashboardApp)
    dashboard.show_feedback = app_module.DashboardApp.show_feedback.__get__(dashboard, app_module.DashboardApp)
    monkeypatch.setattr(app_module.tk, "Entry", lambda *args, **kwargs: FakeWidget())
    monkeypatch.setattr(app_module.tk, "Checkbutton", lambda *args, **kwargs: FakeWidget())
    monkeypatch.setattr(app_module.tk, "BooleanVar", lambda value=False: FakeVar(value))
    return dashboard


def test_internet_search_reviews_and_saves_only_selected_suggestions(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    pending_file.write_text("")
    dashboard = make_headless_app()
    payload = coach.json.dumps([
        {"word": "firewall", "defs": ["n\tA security barrier for network traffic."]},
        {"word": "malware", "defs": ["n\tHarmful software for computers."]},
    ]).encode("utf-8")

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach.urllib.request, "urlopen", lambda url, timeout: FakeResponse(payload))

    suggestions, error = dashboard.fetch_internet_suggestions("cybersecurity")
    dashboard.internet_selection_vars = [
        (FakeVar(True), suggestions[0][0], suggestions[0][1]),
        (FakeVar(False), suggestions[1][0], suggestions[1][1]),
    ]
    dashboard.save_selected_internet_words()

    assert error == ""
    assert suggestions == [
        ("firewall", "A security barrier for network traffic."),
        ("malware", "Harmful software for computers."),
    ]
    assert pending_file.read_text() == "firewall|A security barrier for network traffic.\n"


def test_internet_connection_failure_saves_nothing(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    pending_file.write_text("")
    dashboard = make_headless_app()

    def fail_urlopen(url, timeout):
        raise coach.urllib.error.URLError("offline")

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach.urllib.request, "urlopen", fail_urlopen)

    suggestions, error = dashboard.fetch_internet_suggestions("network")

    assert suggestions == []
    assert error == "Internet connection failed safely. No words were saved."
    assert pending_file.read_text() == ""


def test_internet_malformed_json_saves_nothing(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("")
    pending_file.write_text("")
    dashboard = make_headless_app()

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach.urllib.request, "urlopen", lambda url, timeout: FakeResponse(b"{not json"))

    suggestions, error = dashboard.fetch_internet_suggestions("network")

    assert suggestions == []
    assert error == "Internet response could not be read safely. No words were saved."
    assert pending_file.read_text() == ""


def test_internet_invalid_utf8_saves_nothing(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("")
    pending_file.write_text("")
    dashboard = make_headless_app()

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach.urllib.request, "urlopen", lambda url, timeout: FakeResponse(b"\xff\xfe"))

    suggestions, error = dashboard.fetch_internet_suggestions("network")

    assert suggestions == []
    assert error == "Internet response could not be read safely. No words were saved."
    assert pending_file.read_text() == ""


def test_internet_review_back_returns_to_topic_search_and_preserves_topic(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("")
    pending_file.write_text("")
    dashboard = make_renderable_headless_app(monkeypatch)
    payload = coach.json.dumps([
        {"word": "firewall", "defs": ["n\tA security barrier for network traffic."]},
    ]).encode("utf-8")

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach.urllib.request, "urlopen", lambda url, timeout: FakeResponse(payload))

    dashboard.show_internet_words(push=True)
    dashboard.topic_var.set("cybersecurity")
    dashboard.fetch_internet_words_for_review()

    assert dashboard.current_view == "internet_review"
    assert dashboard.controller.current_screen == "internet_review"

    dashboard.go_back()

    assert dashboard.current_view == "internet_search"
    assert dashboard.controller.current_screen == "internet_search"
    assert dashboard.topic_var.get() == "cybersecurity"


def test_internet_response_skips_invalid_items_and_keeps_valid_suggestion(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("")
    pending_file.write_text("")
    dashboard = make_headless_app()
    payload = coach.json.dumps([
        {"word": 123, "defs": ["n\tBad numeric word."]},
        {"word": None, "defs": ["n\tBad none word."]},
        {"word": ["list"], "defs": ["n\tBad list word."]},
        {"word": "numberdefs", "defs": 123},
        {"word": "nonedef", "defs": [None]},
        {"word": "firewall", "defs": ["n\tA security barrier for network traffic."]},
    ]).encode("utf-8")

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach.urllib.request, "urlopen", lambda url, timeout: FakeResponse(payload))

    suggestions, error = dashboard.fetch_internet_suggestions("cybersecurity")

    assert error == ""
    assert suggestions == [("firewall", "A security barrier for network traffic.")]
    assert pending_file.read_text() == ""


def test_practice_by_level_selection_uses_level_words_and_activity_label(monkeypatch, tmp_path):
    meanings_file = tmp_path / "meanings.txt"
    meanings_file.write_text("router|A network device.\n")
    dashboard = make_headless_app()
    spoken = []
    saved = []

    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "pronounce_word", spoken.append)
    monkeypatch.setattr(coach, "save_missed_word", lambda word: None)
    monkeypatch.setattr(coach, "save_score", lambda score, total, activity: saved.append((score, total, activity)))

    dashboard.start_practice_level("easy", ["router"])
    dashboard.active_session.submit_answer("router", expected_word=dashboard.current_prompt.expected_word)

    assert dashboard.active_session.words == ["router"]
    assert dashboard.active_session.activity_label == "Practice by Level: Easy"
    assert saved == [(1, 1, "Practice by Level: Easy")]


def test_spelling_test_accepts_count_above_five(monkeypatch):
    dashboard = make_headless_app()
    dashboard.amount_var.set("6")
    dashboard.spelling_test_words = ["one", "two", "three", "four", "five", "six"]
    monkeypatch.setattr(coach, "pronounce_word", lambda word: None)
    monkeypatch.setattr(coach, "save_missed_word", lambda word: None)
    monkeypatch.setattr(coach, "save_score", lambda score, total, activity: None)

    dashboard.start_spelling_test_from_amount()

    assert dashboard.active_session.words == ["one", "two", "three", "four", "five", "six"]


def test_spelling_test_rejects_count_above_available_total(monkeypatch):
    dashboard = make_headless_app()
    dashboard.amount_var.set("7")
    dashboard.spelling_test_words = ["one", "two", "three", "four", "five", "six"]
    errors = []
    monkeypatch.setattr(app_module.messagebox, "showerror", lambda title, message: errors.append((title, message)))

    dashboard.start_spelling_test_from_amount()

    assert dashboard.active_session is None
    assert errors == [("Choose a number", "Choose a number from 1 through 6, or type all.")]


def test_correct_spelling_renders_exactly_once_for_incorrect_feedback():
    dashboard = make_headless_app()
    rendered_text = []
    dashboard.body_text = lambda parent, text: rendered_text.append(text)
    dashboard.controller.add_feedback_to_history(
        "Spelling Test",
        logic.ActivityFeedback(False, "Not quite. Review the correct spelling below.", revealed_word="router", question_number=1, total_questions=1),
        "wrong",
    )

    app_module.DashboardApp.render_activity_history(dashboard)

    assert rendered_text[0].count("router") == 1


def test_repeat_word_is_available_after_incorrect_final_answer():
    dashboard = make_headless_app()
    buttons = []
    dashboard.clear = lambda: None
    dashboard.heading = lambda parent, text: None
    dashboard.update_jump_control_visibility = lambda: None
    dashboard.render_activity_history = lambda: None
    dashboard.scroll_to_active_if_requested = lambda: None
    dashboard.make_button = lambda parent, text, command, enabled=True: buttons.append(text)
    dashboard.active_session = logic.SpellingTestSession(["router"], lambda word: None, lambda score, total, activity: None, lambda word: None)
    dashboard.active_session.start()
    feedback = dashboard.active_session.submit_answer("wrong", expected_word="router")

    app_module.DashboardApp.show_feedback(dashboard, feedback)

    assert feedback.finished is True
    assert "Repeat Word" in buttons
    assert "Return Home" in buttons


def test_add_word_preserves_legacy_meaning_lines(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    words_file.write_text("router\n")
    legacy_text = "legacy meaning without separator\nrouter|A network device.\n"
    meanings_file.write_text(legacy_text)
    dashboard = make_headless_app()
    dashboard.word_var.set("firewall")
    dashboard.meaning_var.set("A security barrier.")

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))

    dashboard.save_new_word()

    assert meanings_file.read_text() == legacy_text + "firewall|A security barrier.\n"


def test_approve_pending_words_preserves_legacy_meaning_lines(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    legacy_text = "legacy meaning without separator\nrouter|A network device.\n"
    meanings_file.write_text(legacy_text)
    pending_file.write_text("firewall|A security barrier.\n")
    dashboard = make_headless_app()
    dashboard.pending_selection_vars = [(FakeVar(True), "firewall", "A security barrier.")]

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))

    dashboard.approve_selected_pending_words()

    assert meanings_file.read_text() == legacy_text + "firewall|A security barrier.\n"


def assert_back_sequence_preserves_feedback_and_current_word(dashboard, first_answer):
    dashboard.show_activity_prompt(dashboard.current_prompt, push=True, add_to_history=True)
    dashboard.answer_var.set(first_answer)
    dashboard.submit_answer()

    assert dashboard.current_view == "feedback"
    assert dashboard.controller.current_screen == "feedback"

    dashboard.go_back()

    assert dashboard.current_view == "feedback"
    assert dashboard.controller.current_screen == "feedback"

    dashboard.next_question()

    assert dashboard.current_view == "activity_prompt"
    assert dashboard.controller.current_screen == "activity_prompt"
    assert dashboard.current_prompt.expected_word == "firewall"

    dashboard.go_back()

    assert dashboard.current_view == "feedback"
    assert dashboard.controller.current_screen == "feedback"

    dashboard.next_question()

    assert dashboard.current_view == "activity_prompt"
    assert dashboard.controller.current_screen == "activity_prompt"
    assert dashboard.current_prompt.expected_word == "firewall"
    assert dashboard.active_session.current_word == "firewall"


def test_random_practice_back_after_answer_does_not_restore_editable_old_prompt(monkeypatch):
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.active_session = logic.RandomPracticeSession(
        ["router", "firewall"],
        {"router": "A network device.", "firewall": "A security barrier."},
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    dashboard.current_prompt = dashboard.active_session.start()

    assert_back_sequence_preserves_feedback_and_current_word(dashboard, "router")


def test_spelling_test_back_after_answer_does_not_restore_editable_old_prompt(monkeypatch):
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.active_session = logic.SpellingTestSession(
        ["router", "firewall"],
        save_missed_word=lambda word: None,
        save_score=lambda score, total, activity: None,
        pronounce_word=lambda word: None,
    )
    dashboard.current_prompt = dashboard.active_session.start()

    assert_back_sequence_preserves_feedback_and_current_word(dashboard, "router")


def test_spacing_preserves_internet_search_topic(monkeypatch):
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.current_view = "internet_search"
    dashboard.controller.replace_screen("internet_search")
    dashboard.topic_var.set("cybersecurity")

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.current_view == "internet_search"
    assert dashboard.controller.current_screen == "internet_search"
    assert dashboard.topic_var.get() == "cybersecurity"


def test_spacing_preserves_internet_review_suggestions_and_selection(monkeypatch):
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.current_view = "internet_review"
    dashboard.controller.replace_screen("internet_review")
    dashboard.internet_suggestions = [("firewall", "A barrier."), ("malware", "Harmful software.")]
    dashboard.internet_selection_vars = [(FakeVar(True), "firewall", "A barrier."), (FakeVar(False), "malware", "Harmful software.")]

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.current_view == "internet_review"
    assert dashboard.controller.current_screen == "internet_review"
    assert [(var.get(), word, meaning) for var, word, meaning in dashboard.internet_selection_vars] == [
        (True, "firewall", "A barrier."),
        (False, "malware", "Harmful software."),
    ]


def test_spacing_preserves_pending_selection(monkeypatch, tmp_path):
    pending_file = tmp_path / "pending_words.txt"
    pending_file.write_text("firewall|A barrier.\nmalware|Harmful software.\n")
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.current_view = "approve_pending_words"
    dashboard.controller.replace_screen("approve_pending_words")
    dashboard.pending_selection_vars = [
        (FakeVar(False), "firewall", "A barrier.", "firewall|A barrier.\n"),
        (FakeVar(True), "malware", "Harmful software.", "malware|Harmful software.\n"),
    ]
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.current_view == "approve_pending_words"
    assert dashboard.controller.current_screen == "approve_pending_words"
    assert [(var.get(), word) for var, word, meaning, raw_line in dashboard.pending_selection_vars] == [
        (False, "firewall"),
        (True, "malware"),
    ]


def test_spacing_preserves_pending_words_screen(monkeypatch, tmp_path):
    pending_file = tmp_path / "pending_words.txt"
    pending_file.write_text("firewall|A barrier.\n")
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.current_view = "pending_words"
    dashboard.controller.replace_screen("pending_words")
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.current_view == "pending_words"
    assert dashboard.controller.current_screen == "pending_words"


def test_spacing_preserves_progress_report_screen(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    missed_file = tmp_path / "missed_words.txt"
    pending_file = tmp_path / "pending_words.txt"
    score_file = tmp_path / "score_history.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    missed_file.write_text("")
    pending_file.write_text("")
    score_file.write_text("")
    dashboard = make_renderable_headless_app(monkeypatch)
    dashboard.current_view = "progress_report"
    dashboard.controller.replace_screen("progress_report")
    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "MISSED_WORDS_FILE", str(missed_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))
    monkeypatch.setattr(coach, "SCORE_HISTORY_FILE", str(score_file))

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.current_view == "progress_report"
    assert dashboard.controller.current_screen == "progress_report"


def test_spacing_preserves_feedback_screen(monkeypatch):
    dashboard = make_renderable_headless_app(monkeypatch)
    feedback = logic.ActivityFeedback(False, "Not quite. Review the correct spelling below.", revealed_word="router", question_number=1, total_questions=1)
    dashboard.current_view = "feedback"
    dashboard.controller.current_feedback = feedback
    dashboard.active_session = logic.SpellingTestSession(["router"], lambda word: None, lambda score, total, activity: None, lambda word: None)
    dashboard.controller.replace_screen("feedback")

    app_module.DashboardApp.increase_spacing(dashboard)

    assert dashboard.current_view == "feedback"
    assert dashboard.controller.current_screen == "feedback"
    assert dashboard.controller.current_feedback is feedback


def test_approve_selected_pending_words_preserves_unrelated_pending_lines_exactly(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    pending_text = (
        "firewall|A security barrier.\n"
        "\n"
        "legacy pending line without separator\n"
        "malformed|record|with|extra pipes\n"
        "malware|Harmful software.\n"
    )
    pending_file.write_text(pending_text)
    dashboard = make_headless_app()
    dashboard.pending_selection_vars = [
        (FakeVar(True), "firewall", "A security barrier.", "firewall|A security barrier.\n"),
    ]

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))

    dashboard.approve_selected_pending_words()

    assert pending_file.read_text() == (
        "\n"
        "legacy pending line without separator\n"
        "malformed|record|with|extra pipes\n"
        "malware|Harmful software.\n"
    )


def test_approve_selected_pending_words_preserves_crlf_unrelated_lines(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    pending_file.write_bytes(
        b"firewall|A security barrier.\r\n"
        b"\r\n"
        b"legacy pending line without separator\r\n"
        b"malformed|record|with|extra pipes\r\n"
        b"malware|Harmful software.\r\n"
    )
    dashboard = make_headless_app()
    dashboard.pending_selection_vars = [
        (FakeVar(True), "firewall", "A security barrier.", "firewall|A security barrier.\r\n"),
    ]

    monkeypatch.setattr(coach, "WORDS_FILE", str(words_file))
    monkeypatch.setattr(coach, "MEANINGS_FILE", str(meanings_file))
    monkeypatch.setattr(coach, "PENDING_WORDS_FILE", str(pending_file))

    dashboard.approve_selected_pending_words()

    assert pending_file.read_bytes() == (
        b"\r\n"
        b"legacy pending line without separator\r\n"
        b"malformed|record|with|extra pipes\r\n"
        b"malware|Harmful software.\r\n"
    )
