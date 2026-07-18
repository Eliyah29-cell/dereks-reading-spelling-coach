from dataclasses import dataclass
import random
from typing import Callable, Sequence


@dataclass
class ActivityPrompt:
    word: str | None
    meaning: str
    word_visible: bool
    instruction: str
    question_number: int
    total_questions: int
    expected_word: str | None = None


@dataclass
class ActivityFeedback:
    correct: bool
    message: str
    revealed_word: str | None = None
    finished: bool = False
    question_number: int = 0
    total_questions: int = 0
    final_score: int | None = None
    final_total: int | None = None


@dataclass
class ActivityHistoryItem:
    item_type: str
    activity_label: str
    question_number: int
    total_questions: int
    instruction: str = ""
    visible_word: str | None = None
    meaning: str = ""
    submitted_answer: str | None = None
    feedback_message: str = ""
    revealed_word: str | None = None
    score: int | None = None
    total_answered: int | None = None


@dataclass
class DisplaySettings:
    font_size: int = 18
    spacing: int = 12
    high_contrast: bool = False


class AutoScrollState:
    def __init__(self):
        self.auto_scroll_paused = False
        self.should_show_jump_control = False
        self.scroll_to_active_requested = False

    def reset_for_new_activity(self):
        self.auto_scroll_paused = False
        self.should_show_jump_control = False
        self.scroll_to_active_requested = False

    def add_active_output(self) -> bool:
        if self.auto_scroll_paused:
            self.should_show_jump_control = True
            self.scroll_to_active_requested = False
            return False
        self.should_show_jump_control = False
        self.scroll_to_active_requested = True
        return True

    def manual_scroll_up(self):
        self.auto_scroll_paused = True
        self.should_show_jump_control = True
        self.scroll_to_active_requested = False

    def manual_scroll_to_bottom(self):
        self.auto_scroll_paused = False
        self.should_show_jump_control = False
        self.scroll_to_active_requested = False

    def jump_to_current_question(self):
        self.auto_scroll_paused = False
        self.should_show_jump_control = False
        self.scroll_to_active_requested = True

    def mark_scrolled_to_active(self):
        self.scroll_to_active_requested = False


class DashboardController:
    functional_activities = {
        "practice_all_words",
        "spelling_test",
        "random_practice",
        "practice_by_level",
        "practice_missed_words",
        "add_word",
        "word_list",
        "word_meanings",
        "pronounce_word",
        "internet_words",
        "pending_words",
        "approve_pending_words",
        "missed_words",
        "clear_missed_words",
        "score_history",
        "progress_report",
        "home",
        "exit",
    }

    def __init__(self):
        self.active_activity: str | None = None
        self.current_screen = "home"
        self.back_stack: list[str] = []
        self.display_settings = DisplaySettings()
        self.current_feedback: ActivityFeedback | None = None
        self.activity_history: list[ActivityHistoryItem] = []

    def home_model(self) -> dict[str, dict[str, str]]:
        return {
            "Practice": {
                "Practice All Words": "practice_all_words",
                "Spelling Test": "spelling_test",
                "Random Practice": "random_practice",
                "Practice by Level": "practice_by_level",
                "Practice Missed Words": "practice_missed_words",
            },
            "Word Library": {
                "Add a New Word": "add_word",
                "Show Word List": "word_list",
                "Show Word Meanings": "word_meanings",
                "Pronounce a Word": "pronounce_word",
                "Get New Words from the Internet": "internet_words",
                "Show Pending Words": "pending_words",
                "Approve Pending Words": "approve_pending_words",
            },
            "Review and Progress": {
                "Show Missed Words": "missed_words",
                "Clear Missed Words": "clear_missed_words",
                "Score History": "score_history",
                "Progress Report": "progress_report",
            },
            "Application": {
                "Return Home": "home",
                "Exit Dashboard": "exit",
            },
        }

    def is_functional(self, activity_name: str) -> bool:
        return activity_name in self.functional_activities

    def functional_control_labels(self) -> list[str]:
        labels = []
        for controls in self.home_model().values():
            for label, activity in controls.items():
                if self.is_functional(activity):
                    labels.append(label)
        return labels

    def unfinished_control_labels(self) -> list[str]:
        labels = []
        for controls in self.home_model().values():
            for label, activity in controls.items():
                if not self.is_functional(activity):
                    labels.append(label)
        return labels

    def open_activity(self, activity_name: str):
        self.active_activity = activity_name
        self.current_screen = activity_name

    def go_home(self):
        self.active_activity = None
        self.current_screen = "home"
        self.back_stack.clear()
        self.current_feedback = None

    def push_screen(self, screen_name: str):
        if self.current_screen != screen_name:
            self.back_stack.append(self.current_screen)
        self.current_screen = screen_name

    def replace_screen(self, screen_name: str):
        self.current_screen = screen_name

    def back_to_random_choices_from_amount(self):
        self.back_stack.clear()
        self.current_screen = "random_menu"

    def back(self) -> str:
        if self.back_stack:
            self.current_screen = self.back_stack.pop()
        else:
            self.go_home()
        return self.current_screen

    def exit_dashboard(self) -> str:
        self.active_activity = None
        self.current_screen = "exit"
        return "exit"

    def update_display_settings(self, font_size=None, spacing=None, high_contrast=None):
        if font_size is not None:
            self.display_settings.font_size = font_size
        if spacing is not None:
            self.display_settings.spacing = spacing
        if high_contrast is not None:
            self.display_settings.high_contrast = high_contrast

    def start_activity_history(self):
        self.activity_history = []
        self.current_feedback = None

    def add_prompt_to_history(self, activity_label: str, prompt: ActivityPrompt):
        self.activity_history.append(ActivityHistoryItem(
            item_type="prompt",
            activity_label=activity_label,
            question_number=prompt.question_number,
            total_questions=prompt.total_questions,
            instruction=prompt.instruction,
            visible_word=prompt.word if prompt.word_visible else None,
            meaning=prompt.meaning if prompt.word_visible else "",
        ))

    def add_feedback_to_history(self, activity_label: str, feedback: ActivityFeedback, submitted_answer: str):
        self.current_feedback = feedback
        self.current_screen = "feedback"
        self.activity_history.append(ActivityHistoryItem(
            item_type="feedback",
            activity_label=activity_label,
            question_number=feedback.question_number,
            total_questions=feedback.total_questions,
            submitted_answer=submitted_answer,
            feedback_message=feedback.message,
            revealed_word=feedback.revealed_word,
            score=feedback.final_score,
            total_answered=feedback.final_total,
        ))


def select_random_words(words: Sequence[str], amount: int, random_sample: Callable[[Sequence[str], int], list[str]] | None = None) -> list[str]:
    clean_words = [word for word in words if word]
    if not clean_words:
        return []
    amount = max(1, min(amount, len(clean_words)))
    if random_sample is None:
        random_sample = random.sample
    return list(random_sample(clean_words, amount))


def validate_random_practice_amount(amount_text: str, maximum: int) -> tuple[bool, int | None, str]:
    message = f"Choose a number from 1 through {maximum}."
    if maximum < 1:
        return False, None, "No words are available."
    if not amount_text.strip():
        return False, None, message
    try:
        amount = int(amount_text.strip())
    except ValueError:
        return False, None, message
    if amount < 1 or amount > maximum:
        return False, None, message
    return True, amount, ""


def prepare_spelling_test_words(words: Sequence[str], shuffle_words: Callable[[list[str]], None] | None = None) -> list[str]:
    test_words = [word for word in words if word]
    if shuffle_words is None:
        shuffle_words = random.shuffle
    shuffle_words(test_words)
    return test_words


class MultiWordActivity:
    activity_label = "Activity"

    def __init__(
        self,
        words: list[str],
        save_missed_word: Callable[[str], None],
        save_score: Callable[[int, int, str], None],
        pronounce_word: Callable[[str], None],
    ):
        self.words = [word for word in words if word]
        self.save_missed_word = save_missed_word
        self.save_score = save_score
        self.pronounce_word = pronounce_word
        self.index = 0
        self.score = 0
        self.answered_count = 0
        self.finished = False
        self.score_saved = False
        self.awaiting_feedback_acknowledgement = False
        self.last_answered_word: str | None = None

    @property
    def total_questions(self) -> int:
        return len(self.words)

    @property
    def question_number(self) -> int:
        if not self.words:
            return 0
        return min(self.index + 1, len(self.words))

    @property
    def current_word(self) -> str | None:
        if self.finished or self.index >= len(self.words):
            return None
        return self.words[self.index]

    def repeat_word(self):
        word = self.last_answered_word if self.awaiting_feedback_acknowledgement else self.current_word
        if word:
            self.pronounce_word(word)

    def advance_after_feedback(self):
        self.awaiting_feedback_acknowledgement = False
        self._save_score_once_if_finished()

    def _save_score_once_if_finished(self):
        if self.index >= len(self.words):
            self.finished = True
            if not self.score_saved:
                self.save_score(self.score, self.answered_count, self.activity_label)
                self.score_saved = True

    def submit_answer(self, answer: str, expected_word: str | None = None) -> ActivityFeedback:
        word = self.current_word
        if word is None:
            return ActivityFeedback(False, "This activity is finished.", finished=True, question_number=self.question_number, total_questions=self.total_questions)
        if expected_word is not None and expected_word != word:
            return ActivityFeedback(False, "That old question is no longer active. Please answer the current word.", question_number=self.question_number, total_questions=self.total_questions)

        current_number = self.question_number
        answer = answer.strip().lower()
        correct = answer == word.lower()
        self.answered_count += 1
        self.last_answered_word = word
        if correct:
            self.score += 1
            message = "Correct! Great job."
            revealed_word = None
        else:
            self.save_missed_word(word)
            message = f"Not quite. The correct spelling is: {word}"
            revealed_word = word

        self.index += 1
        self.awaiting_feedback_acknowledgement = True
        self._save_score_once_if_finished()
        return ActivityFeedback(correct, message, revealed_word, self.finished, current_number, self.total_questions, self.score if self.finished else None, self.answered_count if self.finished else None)


class PracticeWordsSession(MultiWordActivity):
    activity_label = "Practice All Words"

    def __init__(self, words, meanings, save_missed_word, save_score, pronounce_word, activity_label=None):
        super().__init__(words, save_missed_word, save_score, pronounce_word)
        self.meanings = meanings
        if activity_label:
            self.activity_label = activity_label

    def start(self) -> ActivityPrompt:
        word = self.current_word
        if not word:
            self.finished = True
            return ActivityPrompt(None, "", True, "No words are available.", 0, 0)
        self.pronounce_word(word)
        return ActivityPrompt(
            word,
            self.meanings.get(word, "No meaning saved yet."),
            True,
            "Read the word and meaning, then type the word.",
            self.question_number,
            self.total_questions,
            word,
        )


class RandomPracticeSession(MultiWordActivity):
    activity_label = "Random Practice"

    def __init__(self, words, meanings, save_missed_word, save_score, pronounce_word):
        super().__init__(words, save_missed_word, save_score, pronounce_word)
        self.meanings = meanings

    def start(self) -> ActivityPrompt:
        word = self.current_word
        if not word:
            self.finished = True
            return ActivityPrompt(None, "", True, "No words are available.", 0, 0)
        self.pronounce_word(word)
        return ActivityPrompt(
            word,
            self.meanings.get(word, "No meaning saved yet."),
            True,
            "Read the word and meaning, then type the word.",
            self.question_number,
            self.total_questions,
            word,
        )


class SpellingTestSession(MultiWordActivity):
    activity_label = "Spelling Test"

    def start(self) -> ActivityPrompt:
        word = self.current_word
        if not word:
            self.finished = True
            return ActivityPrompt(None, "", False, "No words are available.", 0, 0)
        self.pronounce_word(word)
        return ActivityPrompt(None, "", False, "Listen to the word, then spell it from memory.", self.question_number, self.total_questions, word)


class AutoScrollEventController:
    def __init__(self, auto_scroll_state: AutoScrollState):
        self.auto_scroll_state = auto_scroll_state

    def mouse_wheel(self, delta: int, in_activity: bool):
        if in_activity and delta > 0:
            self.auto_scroll_state.manual_scroll_up()

    def linux_button_4(self, in_activity: bool):
        if in_activity:
            self.auto_scroll_state.manual_scroll_up()

    def keyboard_scroll(self, key_name: str, in_activity: bool):
        if in_activity and key_name in ["Prior", "Home"]:
            self.auto_scroll_state.manual_scroll_up()

    def scrollbar_drag(self, previous_fraction: float, current_fraction: float, in_activity: bool):
        if in_activity and current_fraction < previous_fraction:
            self.auto_scroll_state.manual_scroll_up()

    def downward_scroll_finished_at_bottom(self, at_bottom: bool):
        if at_bottom:
            self.auto_scroll_state.manual_scroll_to_bottom()

    def jump_to_current_question(self):
        self.auto_scroll_state.jump_to_current_question()
