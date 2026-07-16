import dashboard
import reading_spelling_coach as coach


def files(monkeypatch, tmp_path):
    words=tmp_path/'words.txt'; meanings=tmp_path/'meanings.txt'; missed=tmp_path/'missed.txt'; pending=tmp_path/'pending.txt'; scores=tmp_path/'scores.txt'
    words.write_text('computer\nrouter\nfirewall\n')
    meanings.write_text('computer|An electronic machine.\nA device that sends network traffic.\nmalformed\n')
    pending.write_text('switch|A device that connects network devices.\nrouter|Duplicate router.\n')
    monkeypatch.setattr(coach,'WORDS_FILE',str(words)); monkeypatch.setattr(coach,'MEANINGS_FILE',str(meanings)); monkeypatch.setattr(coach,'MISSED_WORDS_FILE',str(missed)); monkeypatch.setattr(coach,'PENDING_WORDS_FILE',str(pending)); monkeypatch.setattr(coach,'SCORE_HISTORY_FILE',str(scores))
    return words,meanings,missed,pending,scores


def controller(monkeypatch, tmp_path):
    files(monkeypatch,tmp_path); spoken=[]
    c=dashboard.DashboardController(spoken.append); c.state.words=coach.load_words(); return c, spoken


def test_all_17_menu_functions_present(monkeypatch,tmp_path):
    c,_=controller(monkeypatch,tmp_path)
    assert len(c.menu_functions()) == 17
    assert 'Exit Dashboard' in c.menu_functions()


def test_spacing_preserves_screen_and_activity(monkeypatch,tmp_path):
    c,_=controller(monkeypatch,tmp_path); c.start_practice(['router'],'Practice All Words')
    before=(c.state.screen,c.state.activity,c.state.current_word); old=c.state.spacing
    c.increase_spacing(); assert c.state.spacing > old
    c.decrease_spacing(); assert c.state.spacing == old
    assert (c.state.screen,c.state.activity,c.state.current_word)==before


def test_meaning_recovery_from_malformed_orphan_line(monkeypatch,tmp_path):
    c,_=controller(monkeypatch,tmp_path)
    text=c.show_meanings()
    assert 'router: A device that sends network traffic.' in text
    assert 'firewall: No meaning saved yet.' in text


def test_incorrect_feedback_once_and_repeat_after_miss(monkeypatch,tmp_path):
    c,spoken=controller(monkeypatch,tmp_path); c.start_practice(['router'],'Random Practice')
    feedback=c.submit_answer('rooter')
    assert feedback.count('router') == 1
    assert 'Your answer: rooter' in feedback
    c.repeat_word(); assert spoken[-1] == 'router'


def test_correct_feedback_and_score_save_short_spelling(monkeypatch,tmp_path):
    _,_,_,_,scores=files(monkeypatch,tmp_path); c=dashboard.DashboardController(lambda w: None); c.state.words=coach.load_words()
    c.start_spelling_test('1'); word=c.state.current_word; c.submit_answer(word); done=c.next_word_or_finish()
    assert 'Score: 1 out of 1' in done
    text=scores.read_text(); assert 'Activity: Spelling Test' in text and 'Score: 1 out of 1' in text


def test_full_spelling_and_invalid_count(monkeypatch,tmp_path):
    c,_=controller(monkeypatch,tmp_path)
    assert 'Please enter' in c.start_spelling_test('abc')
    assert 'Choose 1 to' in c.start_spelling_test('0')
    c.start_spelling_test('all'); assert c.state.total == 3


def test_random_practice_validation_and_missed_save(monkeypatch,tmp_path):
    _,_,missed,_,scores=files(monkeypatch,tmp_path); c=dashboard.DashboardController(lambda w: None); c.state.words=coach.load_words()
    assert 'Choose 1' in c.random_practice('all','0')
    assert 'Please enter' in c.random_practice('all','x')
    c.random_practice('all','1'); c.submit_answer('wrong'); c.next_word_or_finish()
    assert missed.read_text().strip() in {'computer','router','firewall'}
    assert 'Activity: Random Practice' in scores.read_text()


def test_lists_clear_confirmation_add_duplicate_pronounce(monkeypatch,tmp_path):
    c,spoken=controller(monkeypatch,tmp_path); coach.save_missed_word('router')
    assert 'router' in c.show_word_list(); assert 'router' in c.show_missed_words()
    assert 'not cleared' in c.clear_missed_words(False); assert coach.load_missed_words()==['router']
    assert 'cleared' in c.clear_missed_words(True); assert coach.load_missed_words()==[]
    assert 'valid' in c.add_new_word('')
    assert 'already' in c.add_new_word('router')
    assert 'Added' in c.add_new_word('keyboard')
    assert 'No word' in c.pronounce(' ')
    c.pronounce('router'); assert spoken[-1]=='router'


def test_practice_by_level_missed_empty_data_and_missing_files(monkeypatch,tmp_path):
    c,_=controller(monkeypatch,tmp_path)
    assert 'valid level' in c.practice_by_level('bad')
    c.practice_by_level('easy'); assert c.state.activity == 'Practice by Level: easy'
    monkeypatch.setattr(coach,'MISSED_WORDS_FILE',str(tmp_path/'missing.txt'))
    assert 'No words' in c.practice_missed_words()


def test_score_history_old_unlabeled_readable(monkeypatch,tmp_path):
    _,_,_,_,scores=files(monkeypatch,tmp_path); scores.write_text('2026-01-01 01:00 PM | Score: 2 out of 3\n')
    c,_=controller(monkeypatch,tmp_path); text=c.score_history()
    assert 'Activity: Unlabeled' in text and 'Date/Time:' in text and 'Score:2 out of 3' in text


def test_pending_approval_preserves_unapproved_and_duplicates(monkeypatch,tmp_path):
    words,meanings,_,pending,_=files(monkeypatch,tmp_path); c,_=controller(monkeypatch,tmp_path)
    assert 'switch|' in c.pending_internet_words()
    assert 'Approved 1' in c.approve_selected_pending([0,1])
    assert 'switch' in words.read_text(); assert 'switch|A device' in meanings.read_text()
    assert 'router|Duplicate' in pending.read_text()


def test_internet_failure_progress_navigation_accessibility_exit(monkeypatch,tmp_path):
    c,_=controller(monkeypatch,tmp_path)
    def fail(topic): raise OSError('offline')
    assert 'Internet error' in c.internet_words(fail)
    assert 'Total words:' in c.progress_report()
    c.state.screen='practice'; c.home(); assert c.back() == 'practice'
    c.increase_text(); c.decrease_text(); c.toggle_high_contrast(); assert isinstance(c.state.high_contrast,bool)
    assert 'closed' in c.exit_dashboard(); assert c.state.closed is True
