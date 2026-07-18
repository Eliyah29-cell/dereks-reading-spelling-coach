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
    app.active_session = None
    app.current_prompt = None
    app.current_view = "home"
    app.random_group_words = []
    app.spelling_test_words = []
    app.rendered = []
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
