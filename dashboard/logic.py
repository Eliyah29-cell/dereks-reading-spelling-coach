from __future__ import annotations

from dataclasses import dataclass
import random
import urllib.error
import urllib.request
import json
from typing import Callable, Sequence

import reading_spelling_coach as coach

NO_MEANING = "No meaning saved yet."


@dataclass
class ActivityPrompt:
    word: str | None
    meaning: str
    word_visible: bool
    instruction: str
    question_number: int
    total_questions: int


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


def read_non_empty_lines(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return []


def load_dashboard_meanings(words: Sequence[str] | None = None) -> dict[str, str]:
    words = list(words or coach.load_words())
    meanings: dict[str, str] = {}
    for index, line in enumerate(read_non_empty_lines(coach.MEANINGS_FILE)):
        if "|" in line:
            word, meaning = line.split("|", 1)
            word = word.strip().lower()
            meaning = meaning.strip()
            if word and meaning:
                meanings[word] = meaning
        elif index < len(words):
            meaning = line.strip()
            if meaning and " " in meaning and meaning.endswith((".", "!", "?")):
                meanings.setdefault(words[index].strip().lower(), meaning)
    return meanings


def save_score_with_activity(score: int, total: int, activity: str):
    try:
        coach.save_score(score, total, activity)
        return
    except TypeError:
        pass
    now = coach.datetime.now()
    with open(coach.SCORE_HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(f"Date: {now:%Y-%m-%d} | Time: {now:%I:%M %p} | Activity: {activity} | Score: {score} out of {total}\n")


def parse_score_line(line: str) -> tuple[str, str, str]:
    if "Activity:" in line:
        date_time = "Unknown date/time"
        activity = "Unlabeled activity"
        score = line
        chunks = [chunk.strip() for chunk in line.split("|")]
        date = ""
        time = ""
        for chunk in chunks:
            if chunk.startswith("Date:"):
                date = chunk.replace("Date:", "", 1).strip()
            elif chunk.startswith("Time:"):
                time = chunk.replace("Time:", "", 1).strip()
            elif chunk.startswith("Activity:"):
                activity = chunk.replace("Activity:", "", 1).strip() or "Unlabeled activity"
            elif chunk.startswith("Score:"):
                score = chunk
        date_time = " ".join(part for part in [date, time] if part) or date_time
        return date_time, activity, score
    if "| Score:" in line:
        date_time, score = line.split("| Score:", 1)
        return date_time.strip(), "Unlabeled activity", "Score:" + score.strip()
    return "Unknown date/time", "Unlabeled activity", line


def validate_random_practice_amount(amount_text: str, maximum: int) -> tuple[bool, int | None, str]:
    capped_maximum = min(5, maximum)
    message = f"Choose a number from 1 through {capped_maximum}."
    if capped_maximum < 1:
        return False, None, "No words are available."
    try:
        amount = int(amount_text.strip())
    except ValueError:
        return False, None, message
    if amount < 1 or amount > capped_maximum:
        return False, None, message
    return True, amount, ""


def select_random_words(words: Sequence[str], amount: int, random_sample: Callable[[Sequence[str], int], list[str]] | None = None) -> list[str]:
    clean_words = [word for word in words if word]
    if not clean_words:
        return []
    if random_sample is None:
        random_sample = random.sample
    return list(random_sample(clean_words, min(amount, len(clean_words))))


def prepare_spelling_test_words(words: Sequence[str], count_text: str, shuffle_words: Callable[[list[str]], None] | None = None) -> tuple[bool, list[str], str]:
    clean_words = [word for word in words if word]
    if not clean_words:
        return False, [], "No words are available."
    text = count_text.strip().lower()
    if text == "all":
        count = len(clean_words)
    else:
        try:
            count = int(text)
        except ValueError:
            return False, [], f"Choose 1 through {len(clean_words)}, or All Words."
        if count < 1 or count > len(clean_words):
            return False, [], f"Choose 1 through {len(clean_words)}, or All Words."
    selected = list(clean_words)
    if shuffle_words is None:
        shuffle_words = random.shuffle
    shuffle_words(selected)
    return True, selected[:count], ""


class DashboardController:
    functional_activities = {
        "practice_all_words", "spelling_test", "add_word", "word_list", "practice_missed_words",
        "missed_words", "clear_missed_words", "word_meanings", "practice_by_level", "score_history",
        "exit", "internet_words", "pending_words", "approve_pending_words", "random_practice",
        "progress_report", "pronounce_word", "home",
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
            "Application": {"Return Home": "home", "Exit Dashboard": "exit"},
        }

    def is_functional(self, activity_name: str) -> bool:
        return activity_name in self.functional_activities

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

    def back(self) -> str:
        if self.back_stack:
            self.current_screen = self.back_stack.pop()
        else:
            self.go_home()
        return self.current_screen

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
            item_type="prompt", activity_label=activity_label, question_number=prompt.question_number,
            total_questions=prompt.total_questions, instruction=prompt.instruction,
            visible_word=prompt.word if prompt.word_visible else None,
            meaning=prompt.meaning if prompt.word_visible else "",
        ))

    def add_feedback_to_history(self, activity_label: str, feedback: ActivityFeedback, submitted_answer: str):
        self.current_feedback = feedback
        self.current_screen = "feedback"
        self.activity_history.append(ActivityHistoryItem(
            item_type="feedback", activity_label=activity_label, question_number=feedback.question_number,
            total_questions=feedback.total_questions, submitted_answer=submitted_answer,
            feedback_message=feedback.message, revealed_word=feedback.revealed_word,
            score=feedback.final_score, total_answered=feedback.final_total,
        ))


class MultiWordActivity:
    activity_label = "Activity"

    def __init__(self, words: list[str], save_missed_word, save_score, pronounce_word):
        self.words = [word for word in words if word]
        self.save_missed_word = save_missed_word
        self.save_score = save_score
        self.pronounce_word = pronounce_word
        self.index = 0
        self.score = 0
        self.answered_count = 0
        self.finished = False
        self.score_saved = False
        self.last_word: str | None = None

    @property
    def total_questions(self):
        return len(self.words)

    @property
    def question_number(self):
        return min(self.index + 1, len(self.words)) if self.words else 0

    @property
    def current_word(self):
        if self.finished or self.index >= len(self.words):
            return None
        return self.words[self.index]

    def repeat_word(self):
        word = self.current_word or self.last_word
        if word:
            self.pronounce_word(word)

    def submit_answer(self, answer: str) -> ActivityFeedback:
        word = self.current_word
        if word is None:
            return ActivityFeedback(False, "This activity is finished.", finished=True)
        self.last_word = word
        current_number = self.question_number
        correct = answer.strip().lower() == word.lower()
        self.answered_count += 1
        if correct:
            self.score += 1
            message = "Correct! Great job."
            revealed_word = None
        else:
            self.save_missed_word(word)
            message = "Not quite."
            revealed_word = word
        self.index += 1
        if self.index >= len(self.words):
            self.finished = True
            if not self.score_saved:
                self.save_score(self.score, self.answered_count, self.activity_label)
                self.score_saved = True
        return ActivityFeedback(correct, message, revealed_word, self.finished, current_number, self.total_questions, self.score if self.finished else None, self.answered_count if self.finished else None)


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
        return ActivityPrompt(word, self.meanings.get(word, NO_MEANING), True, "Read the word and meaning, then type the word.", self.question_number, self.total_questions)


class SpellingTestSession(MultiWordActivity):
    activity_label = "Spelling Test"

    def start(self) -> ActivityPrompt:
        word = self.current_word
        if not word:
            self.finished = True
            return ActivityPrompt(None, "", False, "No words are available.", 0, 0)
        self.pronounce_word(word)
        return ActivityPrompt(None, "", False, "Listen to the word, then spell it from memory.", self.question_number, self.total_questions)


class PracticeWordsSession(RandomPracticeSession):
    activity_label = "Practice All Words"

    def __init__(self, words, meanings, save_missed_word, save_score, pronounce_word):
        super().__init__(words, meanings, save_missed_word, save_score, pronounce_word)


class PracticeMissedWordsSession(RandomPracticeSession):
    activity_label = "Practice Missed Words"


class PracticeByLevelSession(RandomPracticeSession):
    def __init__(self, level_name, words, meanings, save_missed_word, save_score, pronounce_word):
        self.activity_label = f"Practice by Level: {level_name}"
        super().__init__(words, meanings, save_missed_word, save_score, pronounce_word)


def add_word_to_bank(word: str) -> tuple[bool, str, list[str]]:
    clean = coach.clean_internet_word(word)
    words = coach.load_words()
    if not clean:
        return False, "Please enter a valid word.", words
    if clean in words:
        return False, "That word is already in the list.", words
    words.append(clean)
    coach.save_words(words)
    return True, f"Added and saved word: {clean}", words


def load_pending_word_records() -> list[tuple[str, str]]:
    records = []
    for line in read_non_empty_lines(coach.PENDING_WORDS_FILE):
        if "|" in line:
            word, meaning = line.split("|", 1)
        else:
            word, meaning = line, "No meaning found yet."
        clean = coach.clean_internet_word(word)
        if clean:
            records.append((clean, meaning.strip()))
    return records


def approve_pending_indices(selected_indices: set[int]) -> tuple[int, list[tuple[str, str]]]:
    pending = load_pending_word_records()
    existing = set(coach.load_words())
    approved: list[tuple[str, str]] = []
    remaining: list[tuple[str, str]] = []
    for index, (word, meaning) in enumerate(pending):
        if index in selected_indices and word not in existing:
            approved.append((word, meaning))
            existing.add(word)
        else:
            remaining.append((word, meaning))
    if approved:
        words = coach.load_words()
        words.extend(word for word, _ in approved)
        coach.save_words(words)
        with open(coach.MEANINGS_FILE, "a", encoding="utf-8") as meanings_file:
            for word, meaning in approved:
                meanings_file.write(f"{word}|{meaning}\n")
    with open(coach.PENDING_WORDS_FILE, "w", encoding="utf-8") as pending_file:
        for word, meaning in remaining:
            pending_file.write(f"{word}|{meaning}\n")
    return len(approved), remaining


def fetch_internet_suggestions(topic: str, opener=urllib.request.urlopen) -> list[tuple[str, str]]:
    query = coach.prepare_internet_search_topic(topic or "computer")
    url = "https://api.datamuse.com/words?" + urllib.parse.urlencode({"ml": query, "md": "d", "max": "10"})
    try:
        with opener(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []
    suggestions = []
    existing = set(coach.load_words())
    pending = {word for word, _ in load_pending_word_records()}
    for item in data:
        word = coach.clean_internet_word(item.get("word", ""))
        defs = item.get("defs", [])
        if not word or word in existing or word in pending or not defs:
            continue
        meaning = coach.clean_definition(defs[0].split("\t", 1)[-1])
        if meaning != "No meaning found yet.":
            suggestions.append((word, meaning))
    return suggestions


def save_selected_suggestions(suggestions: Sequence[tuple[str, str]], selected_indices: set[int]) -> int:
    saved = 0
    existing_pending = {word for word, _ in load_pending_word_records()}
    with open(coach.PENDING_WORDS_FILE, "a", encoding="utf-8") as pending_file:
        for index, (word, meaning) in enumerate(suggestions):
            if index in selected_indices and word not in existing_pending:
                pending_file.write(f"{word}|{meaning}\n")
                saved += 1
    return saved


def build_progress_report() -> list[str]:
    scores = read_non_empty_lines(coach.SCORE_HISTORY_FILE)
    return [
        f"Total words: {len(coach.load_words())}",
        f"Total meanings: {len(read_non_empty_lines(coach.MEANINGS_FILE))}",
        f"Pending internet words: {len(read_non_empty_lines(coach.PENDING_WORDS_FILE))}",
        f"Missed words to practice: {len(coach.load_missed_words())}",
        f"Saved score records: {len(scores)}",
    ]
