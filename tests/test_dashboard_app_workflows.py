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


def test_internet_search_reviews_and_saves_only_selected_suggestions(monkeypatch, tmp_path):
    words_file = tmp_path / "words.txt"
    meanings_file = tmp_path / "meanings.txt"
    pending_file = tmp_path / "pending_words.txt"
    words_file.write_text("router\n")
    meanings_file.write_text("router|A network device.\n")
    pending_file.write_text("")
    dashboard = make_headless_app()
    payload = (
        b'[{"word": "firewall", "defs": ["n\\tA security barrier for network traffic."]},'
        b' {"word": "malware", "defs": ["n\\tHarmful software for computers."]}]'
    )

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
