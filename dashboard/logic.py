from dataclasses import dataclass
from typing import Callable


@dataclass
class ActivityPrompt:
    word: str | None
    meaning: str
    word_visible: bool
    instruction: str


@dataclass
class ActivityFeedback:
    correct: bool
    message: str
    revealed_word: str | None = None
    finished: bool = False


class AutoScrollState:
    def __init__(self):
        self.auto_scroll_paused = False
        self.should_show_jump_control = False

    def add_active_output(self) -> bool:
        if self.auto_scroll_paused:
            self.should_show_jump_control = True
            return False
        self.should_show_jump_control = False
        return True

    def manual_scroll_up(self):
        self.auto_scroll_paused = True
        self.should_show_jump_control = True

    def jump_to_current_question(self):
        self.auto_scroll_paused = False
        self.should_show_jump_control = False


class DashboardController:
    def __init__(self):
        self.active_activity: str | None = None

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

    def open_activity(self, activity_name: str):
        self.active_activity = activity_name

    def go_home(self):
        self.active_activity = None

    def back(self):
        self.go_home()

    def exit_dashboard(self) -> str:
        self.active_activity = None
        return "exit"


class OneWordActivity:
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

    @property
    def current_word(self) -> str | None:
        if self.finished or self.index >= len(self.words):
            return None
        return self.words[self.index]

    def repeat_word(self):
        word = self.current_word
        if word:
            self.pronounce_word(word)

    def _finish_if_needed(self):
        if self.index >= len(self.words):
            self.finished = True
            self.save_score(self.score, self.answered_count, self.activity_label)

    def submit_answer(self, answer: str) -> ActivityFeedback:
        word = self.current_word
        if word is None:
            return ActivityFeedback(False, "This activity is finished.", finished=True)

        answer = answer.strip().lower()
        correct = answer == word.lower()
        self.answered_count += 1
        if correct:
            self.score += 1
            message = "Correct! Great job."
            revealed_word = None
        else:
            self.save_missed_word(word)
            message = f"Not quite. The correct spelling is: {word}"
            revealed_word = word

        self.index += 1
        self._finish_if_needed()
        return ActivityFeedback(correct, message, revealed_word, self.finished)


class RandomPracticeSession(OneWordActivity):
    activity_label = "Random Practice"

    def __init__(self, words, meanings, save_missed_word, save_score, pronounce_word):
        super().__init__(words, save_missed_word, save_score, pronounce_word)
        self.meanings = meanings

    def start(self) -> ActivityPrompt:
        word = self.current_word
        if not word:
            self.finished = True
            return ActivityPrompt(None, "", True, "No words are available.")
        self.pronounce_word(word)
        return ActivityPrompt(word, self.meanings.get(word, "No meaning saved yet."), True, "Read the word and meaning, then type the word.")


class SpellingTestSession(OneWordActivity):
    activity_label = "Spelling Test"

    def start(self) -> ActivityPrompt:
        word = self.current_word
        if not word:
            self.finished = True
            return ActivityPrompt(None, "", False, "No words are available.")
        self.pronounce_word(word)
        return ActivityPrompt(None, "", False, "Listen to the word, then spell it from memory.")
