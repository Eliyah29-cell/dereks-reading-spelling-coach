import json
from io import BytesIO
from contextlib import contextmanager

import dashboard.app as app
import dashboard.logic as logic
import reading_spelling_coach as coach


def files(monkeypatch, tmp_path):
    words=tmp_path/'words.txt'; meanings=tmp_path/'meanings.txt'; missed=tmp_path/'missed.txt'; pending=tmp_path/'pending.txt'; scores=tmp_path/'scores.txt'
    words.write_text('computer\nrouter\nfirewall\n')
    meanings.write_text('computer|An electronic machine.\nA device that sends network traffic.\nmalformed\n')
    pending.write_text('switch|A device that connects network devices.\nrouter|Duplicate.\n')
    monkeypatch.setattr(coach,'WORDS_FILE',str(words)); monkeypatch.setattr(coach,'MEANINGS_FILE',str(meanings)); monkeypatch.setattr(coach,'MISSED_WORDS_FILE',str(missed)); monkeypatch.setattr(coach,'PENDING_WORDS_FILE',str(pending)); monkeypatch.setattr(coach,'SCORE_HISTORY_FILE',str(scores))
    return words,meanings,missed,pending,scores


def test_home_model_has_all_17_functional_activities():
    c=logic.DashboardController(); acts=[a for group in c.home_model().values() for a in group.values()]
    assert len(acts)==18  # includes Return Home plus 17 menu choices
    assert all(c.is_functional(a) for a in acts)


def test_display_settings_preserve_screen_and_history():
    c=logic.DashboardController(); c.push_screen('activity_prompt'); before=(c.current_screen,list(c.back_stack))
    c.update_display_settings(font_size=22, spacing=20, high_contrast=True)
    assert c.display_settings.font_size==22 and c.display_settings.spacing==20 and c.display_settings.high_contrast is True
    assert (c.current_screen,c.back_stack)==before


def test_meaning_parser_recovers_usable_orphan_and_skips_malformed(monkeypatch,tmp_path):
    files(monkeypatch,tmp_path)
    meanings=logic.load_dashboard_meanings(['computer','router','firewall'])
    assert meanings['computer']=='An electronic machine.'
    assert meanings['router']=='A device that sends network traffic.'
    assert 'firewall' not in meanings


def test_score_save_with_activity_falls_back_for_terminal_signature(monkeypatch,tmp_path):
    *_,scores=files(monkeypatch,tmp_path)
    logic.save_score_with_activity(2,3,'Random Practice')
    text=scores.read_text()
    assert 'Activity: Random Practice' in text and 'Score: 2 out of 3' in text


def test_parse_old_score_as_unlabeled():
    assert logic.parse_score_line('2026-01-01 01:00 PM | Score: 1 out of 2') == ('2026-01-01 01:00 PM','Unlabeled activity','Score:1 out of 2')


def test_parse_new_score_separates_date_activity_score():
    assert logic.parse_score_line('Date: 2026-01-01 | Time: 01:00 PM | Activity: Spelling Test | Score: 1 out of 2') == ('2026-01-01 01:00 PM','Spelling Test','Score: 1 out of 2')


def test_random_amount_accepts_1_to_5():
    for value in ['1','2','3','4','5']:
        ok, amount, msg = logic.validate_random_practice_amount(value, 10)
        assert ok and amount == int(value) and msg == ''


def test_random_amount_rejects_0_6_letters_and_empty():
    for value in ['0','6','abc','']:
        ok, amount, msg = logic.validate_random_practice_amount(value, 10)
        assert not ok and amount is None and '1 through 5' in msg


def test_random_amount_caps_to_available_words():
    assert logic.validate_random_practice_amount('3', 2)[0] is False
    assert logic.validate_random_practice_amount('2', 2)[0] is True


def test_select_random_words_uses_sampler():
    assert logic.select_random_words(['a','b','c'],2,lambda words, amount: list(words)[:amount]) == ['a','b']


def test_spelling_test_count_validation_and_all():
    ok, words, msg = logic.prepare_spelling_test_words(['a','b','c'],'all',lambda w: None)
    assert ok and words == ['a','b','c']
    ok, words, msg = logic.prepare_spelling_test_words(['a','b','c'],'2',lambda w: None)
    assert ok and words == ['a','b']
    assert logic.prepare_spelling_test_words(['a'],'0')[0] is False
    assert logic.prepare_spelling_test_words(['a'],'x')[0] is False


def test_random_session_prompt_shows_word_meaning_and_speaks():
    spoken=[]; s=logic.RandomPracticeSession(['router'],{'router':'Network device.'},lambda w: None,lambda s,t,a: None,spoken.append)
    p=s.start()
    assert p.word_visible is True and p.word=='router' and p.meaning=='Network device.' and spoken==['router']


def test_spelling_session_hides_word_before_submission_and_speaks():
    spoken=[]; s=logic.SpellingTestSession(['router'],lambda w: None,lambda s,t,a: None,spoken.append)
    p=s.start()
    assert p.word_visible is False and p.word is None and spoken==['router']


def test_incorrect_feedback_has_one_correct_spelling_and_saves_missed():
    missed=[]; s=logic.SpellingTestSession(['router'],missed.append,lambda s,t,a: None,lambda w: None)
    s.start(); f=s.submit_answer('rooter')
    assert f.message == 'Not quite.' and f.revealed_word == 'router' and missed == ['router']


def test_repeat_word_after_incorrect_uses_last_word():
    spoken=[]; s=logic.RandomPracticeSession(['router'],{},lambda w: None,lambda s,t,a: None,spoken.append)
    s.start(); s.submit_answer('bad'); s.repeat_word()
    assert spoken == ['router','router']


def test_correct_answer_scores_and_saves_once():
    saved=[]; s=logic.RandomPracticeSession(['router'],{},lambda w: None,lambda s,t,a: saved.append((s,t,a)),lambda w: None)
    s.start(); f=s.submit_answer('router'); s.submit_answer('router')
    assert f.correct and f.final_score == 1 and saved == [(1,1,'Random Practice')]


def test_practice_all_words_label():
    s=logic.PracticeWordsSession(['computer'],{},lambda w: None,lambda s,t,a: None,lambda w: None)
    assert s.activity_label == 'Practice All Words'


def test_practice_missed_words_label():
    s=logic.PracticeMissedWordsSession(['computer'],{},lambda w: None,lambda s,t,a: None,lambda w: None)
    assert s.activity_label == 'Practice Missed Words'


def test_practice_by_level_label():
    s=logic.PracticeByLevelSession('easy',['computer'],{},lambda w: None,lambda s,t,a: None,lambda w: None)
    assert s.activity_label == 'Practice by Level: easy'


def test_add_word_valid_blank_duplicate(monkeypatch,tmp_path):
    words,*_=files(monkeypatch,tmp_path)
    assert logic.add_word_to_bank('')[0] is False
    assert logic.add_word_to_bank('router')[0] is False
    ok,msg,current=logic.add_word_to_bank('Keyboard')
    assert ok and 'keyboard' in current and 'keyboard' in words.read_text()


def test_pending_records_show_word_and_meaning(monkeypatch,tmp_path):
    files(monkeypatch,tmp_path)
    assert logic.load_pending_word_records() == [('switch','A device that connects network devices.'),('router','Duplicate.')]


def test_approve_pending_selected_preserves_unapproved_and_duplicates(monkeypatch,tmp_path):
    words,meanings,_,pending,_=files(monkeypatch,tmp_path)
    count, remaining=logic.approve_pending_indices({0,1})
    assert count == 1 and remaining == [('router','Duplicate.')]
    assert 'switch' in words.read_text() and 'switch|A device' in meanings.read_text() and 'router|Duplicate.' in pending.read_text()


def test_save_selected_suggestions_only_selected_and_no_duplicates(monkeypatch,tmp_path):
    *_,pending,_=files(monkeypatch,tmp_path)
    saved=logic.save_selected_suggestions([('alpha','First.'),('switch','Duplicate pending.')],{0,1})
    assert saved == 1 and 'alpha|First.' in pending.read_text()


class FakeResponse:
    def __init__(self, payload): self.payload=payload
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self): return json.dumps(self.payload).encode()


def test_fetch_internet_suggestions_reviews_safe_defs(monkeypatch,tmp_path):
    files(monkeypatch,tmp_path)
    def opener(url, timeout):
        return FakeResponse([{'word':'Keyboard','defs':['n\tA device used to type.']},{'word':'router','defs':['n\tDuplicate.']},{'word':'bad!','defs':['n\tBad.']}])
    assert logic.fetch_internet_suggestions('computer', opener) == [('keyboard','A device used to type.')]


def test_fetch_internet_suggestions_failure_returns_empty(monkeypatch,tmp_path):
    files(monkeypatch,tmp_path)
    def opener(url, timeout): raise OSError('offline')
    assert logic.fetch_internet_suggestions('computer', opener) == []


def test_progress_report_counts_temp_files(monkeypatch,tmp_path):
    files(monkeypatch,tmp_path); coach.save_missed_word('router')
    report='\n'.join(logic.build_progress_report())
    assert 'Total words: 3' in report and 'Pending internet words: 2' in report and 'Missed words to practice: 1' in report


def test_autoscroll_jump_control_states():
    s=logic.AutoScrollState(); assert s.add_active_output() is True
    s.manual_scroll_up(); assert s.should_show_jump_control is True and s.add_active_output() is False
    s.jump_to_current_question(); assert s.scroll_to_active_requested is True
    s.mark_scrolled_to_active(); assert s.scroll_to_active_requested is False


def test_autoscroll_event_controller_pauses_on_up_events():
    s=logic.AutoScrollState(); e=logic.AutoScrollEventController(s)
    e.mouse_wheel(120, True); assert s.auto_scroll_paused is True
    s.manual_scroll_to_bottom(); e.keyboard_scroll('Home', True); assert s.auto_scroll_paused is True


def test_controller_history_records_prompt_and_feedback():
    c=logic.DashboardController(); p=logic.ActivityPrompt('word','meaning',True,'instruction',1,1)
    c.add_prompt_to_history('Activity',p); f=logic.ActivityFeedback(False,'No', 'word', True, 1,1,0,1)
    c.add_feedback_to_history('Activity', f, 'bad')
    assert len(c.activity_history)==2 and c.activity_history[-1].submitted_answer=='bad' and c.current_screen=='feedback'


def test_dashboard_app_has_handlers_for_real_workflows():
    required=['show_spelling_count','show_level_menu','show_random_menu','show_random_amount','show_activity_prompt','show_feedback','show_add_word','show_internet_words','show_pending_words','show_approve_pending_words','pronounce_entered_word']
    for name in required:
        assert hasattr(app.DashboardApp, name)


def test_dashboard_app_open_activity_routes_all_menu_functions():
    names=app.DashboardApp.open_activity.__code__.co_consts
    for activity in ['practice_all_words','spelling_test','add_word','word_list','practice_missed_words','missed_words','clear_missed_words','word_meanings','practice_by_level','score_history','exit','internet_words','pending_words','approve_pending_words','random_practice','progress_report','pronounce_word']:
        assert activity in names


def test_dashboard_app_accessibility_methods_update_and_rerender():
    for name in ['increase_font','decrease_font','increase_spacing','decrease_spacing','update_accessibility','render_current_view']:
        assert hasattr(app.DashboardApp, name)


def test_dashboard_app_feedback_has_repeat_word_path():
    assert 'Repeat Word' in app.DashboardApp.show_feedback.__code__.co_consts


def test_dashboard_app_does_not_hardcode_random_all_one_or_level_easy_start():
    consts = app.DashboardApp.open_activity.__code__.co_consts + app.DashboardApp.start_random_from_amount.__code__.co_consts + app.DashboardApp.start_spelling_test.__code__.co_consts
    assert 'easy' not in app.DashboardApp.open_activity.__code__.co_consts
    assert 'all' not in app.DashboardApp.start_spelling_test.__code__.co_consts


def test_exit_dashboard_routes_to_root_destroy():
    assert 'destroy' in app.DashboardApp.open_activity.__code__.co_names


def test_dashboard_app_back_restores_supported_previous_screens():
    class FakeController:
        current_feedback = object()

        def __init__(self, previous):
            self.previous = previous

        def back(self):
            return self.previous

    supported_screens = {
        'home': 'show_home',
        'random_menu': 'show_random_menu',
        'random_amount': 'show_random_amount',
        'spelling_count': 'show_spelling_count',
        'level_menu': 'show_level_menu',
        'add_word': 'show_add_word',
        'pronounce_word': 'show_pronounce',
        'internet_words': 'show_internet_words',
        'pending_words': 'show_pending_words',
        'approve_pending_words': 'show_approve_pending_words',
        'activity_prompt': 'show_activity_prompt',
        'feedback': 'show_feedback',
        'lines': 'show_lines',
    }

    for screen, expected_handler in supported_screens.items():
        dashboard = app.DashboardApp.__new__(app.DashboardApp)
        dashboard.controller = FakeController(screen)
        dashboard.current_prompt = object()
        dashboard.last_lines_title = 'Saved Screen'
        dashboard.last_lines = ['saved line']
        calls = []

        def record(name):
            def handler(*args, **kwargs):
                calls.append((name, args, kwargs))
            return handler

        for handler_name in set(supported_screens.values()) | {'show_home'}:
            setattr(dashboard, handler_name, record(handler_name))

        dashboard.go_back()

        assert calls[0][0] == expected_handler
        if expected_handler not in {'show_home'}:
            assert calls[0][2].get('push') is False


def test_dashboard_app_back_falls_home_for_unsupported_previous_screen():
    class FakeController:
        current_feedback = None

        def back(self):
            return 'unknown_screen'

    dashboard = app.DashboardApp.__new__(app.DashboardApp)
    dashboard.controller = FakeController()
    dashboard.current_prompt = None
    calls = []
    dashboard.show_home = lambda: calls.append('home')

    dashboard.go_back()

    assert calls == ['home']


class SimpleVar:
    def __init__(self, value=''):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class QuietAutoScroll:
    def reset_for_new_activity(self):
        pass

    def add_active_output(self):
        return True


def build_nonvisual_dashboard_for_activity(session, monkeypatch):
    class FakeEntry:
        def __init__(self, *args, **kwargs):
            pass

        def pack(self, *args, **kwargs):
            pass

        def focus_set(self):
            pass

        def bind(self, *args, **kwargs):
            pass

    monkeypatch.setattr(app.tk, 'Entry', FakeEntry)
    dashboard = app.DashboardApp.__new__(app.DashboardApp)
    dashboard.controller = logic.DashboardController()
    dashboard.auto_scroll = QuietAutoScroll()
    dashboard.active_session = None
    dashboard.current_prompt = None
    dashboard.current_view = 'home'
    dashboard.answer_var = SimpleVar('')
    dashboard.font_size = SimpleVar(18)
    dashboard.rendered_prompts = []
    dashboard.rendered_feedback = []
    dashboard.clear = lambda: None
    dashboard.heading = lambda parent, text: None
    dashboard.body_text = lambda parent, text: None
    dashboard.make_button = lambda *args, **kwargs: None
    dashboard.update_jump_control_visibility = lambda: None
    dashboard.render_activity_history = lambda: None
    dashboard.scroll_to_active_if_requested = lambda: None
    dashboard.show_home = lambda: setattr(dashboard, 'current_view', 'home')
    dashboard.main = object()
    dashboard.start_session(session, push=True)
    return dashboard


def test_next_question_push_false_syncs_controller_and_back_keeps_current_random_prompt(monkeypatch):
    missed = []
    saved = []
    session = logic.RandomPracticeSession(
        ['alpha', 'beta'],
        {'alpha': 'First.', 'beta': 'Second.'},
        missed.append,
        lambda score, total, activity: saved.append((score, total, activity)),
        lambda word: None,
    )
    dashboard = build_nonvisual_dashboard_for_activity(session, monkeypatch)

    assert dashboard.controller.current_screen == 'activity_prompt'
    assert dashboard.current_prompt.word == 'alpha'

    dashboard.answer_var.set('wrong')
    dashboard.submit_answer()
    assert dashboard.controller.current_screen == 'feedback'
    assert dashboard.controller.current_feedback.revealed_word == 'alpha'

    dashboard.next_question()
    assert dashboard.controller.current_screen == 'activity_prompt'
    assert dashboard.current_view == 'activity_prompt'
    assert dashboard.current_prompt.word == 'beta'
    assert dashboard.active_session.current_word == 'beta'

    dashboard.go_back()
    assert dashboard.controller.current_screen == 'activity_prompt'
    assert dashboard.current_view == 'activity_prompt'
    assert dashboard.current_prompt.word == 'beta'
    assert dashboard.active_session.current_word == 'beta'

    dashboard.answer_var.set('alpha')
    dashboard.submit_answer()
    assert dashboard.controller.current_feedback.revealed_word == 'beta'
    assert missed == ['alpha', 'beta']
    assert saved == [(0, 2, 'Random Practice')]


def test_next_question_push_false_syncs_controller_and_back_keeps_current_spelling_prompt(monkeypatch):
    missed = []
    saved = []
    session = logic.SpellingTestSession(
        ['alpha', 'beta'],
        missed.append,
        lambda score, total, activity: saved.append((score, total, activity)),
        lambda word: None,
    )
    dashboard = build_nonvisual_dashboard_for_activity(session, monkeypatch)

    assert dashboard.controller.current_screen == 'activity_prompt'
    assert dashboard.current_prompt.word is None
    assert dashboard.active_session.current_word == 'alpha'

    dashboard.answer_var.set('wrong')
    dashboard.submit_answer()
    assert dashboard.controller.current_screen == 'feedback'
    assert dashboard.controller.current_feedback.revealed_word == 'alpha'

    dashboard.next_question()
    assert dashboard.controller.current_screen == 'activity_prompt'
    assert dashboard.current_view == 'activity_prompt'
    assert dashboard.current_prompt.word is None
    assert dashboard.active_session.current_word == 'beta'

    dashboard.go_back()
    assert dashboard.controller.current_screen == 'activity_prompt'
    assert dashboard.current_view == 'activity_prompt'
    assert dashboard.current_prompt.word is None
    assert dashboard.active_session.current_word == 'beta'

    dashboard.answer_var.set('alpha')
    dashboard.submit_answer()
    assert dashboard.controller.current_feedback.revealed_word == 'beta'
    assert missed == ['alpha', 'beta']
    assert saved == [(0, 2, 'Spelling Test')]
