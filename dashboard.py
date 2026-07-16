"""Tkinter dashboard and testable logic for Derek's Reading & Spelling Coach."""
from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox, simpledialog
import urllib.error
from dataclasses import dataclass, field
from typing import Callable

import reading_spelling_coach as coach

NO_MEANING = "No meaning saved yet."


def _read_lines(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return []


def parse_meaning_lines(lines: list[str]) -> dict[str, str]:
    """Recover usable word meanings from pipe records and legacy orphan lines."""
    meanings: dict[str, str] = {}
    words = coach.load_words()
    for index, line in enumerate(lines):
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


def load_dashboard_meanings() -> dict[str, str]:
    return parse_meaning_lines(_read_lines(coach.MEANINGS_FILE))


def save_score_with_activity(activity: str, score: int, total: int) -> None:
    now = coach.datetime.now()
    date_text = now.strftime("%Y-%m-%d")
    time_text = now.strftime("%I:%M %p")
    with open(coach.SCORE_HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(f"Date: {date_text} | Time: {time_text} | Activity: {activity} | Score: {score} out of {total}\n")


def parse_score_record(line: str) -> dict[str, str]:
    if "Activity:" in line:
        parts = [part.strip() for part in line.split("|")]
        data = {"date": "Unknown date", "time": "Unknown time", "activity": "Unlabeled", "score": line}
        for part in parts:
            if part.startswith("Date:"):
                data["date"] = part.replace("Date:", "", 1).strip()
            elif part.startswith("Time:"):
                data["time"] = part.replace("Time:", "", 1).strip()
            elif part.startswith("Activity:"):
                data["activity"] = part.replace("Activity:", "", 1).strip() or "Unlabeled"
            elif part.startswith("Score:"):
                data["score"] = part.strip()
        return data
    if "| Score:" in line:
        date_time, score = line.split("| Score:", 1)
        return {"date": date_time.strip(), "time": "", "activity": "Unlabeled", "score": "Score:" + score.strip()}
    return {"date": "Unknown date", "time": "", "activity": "Unlabeled", "score": line}


@dataclass
class DashboardState:
    words: list[str] = field(default_factory=coach.load_words)
    screen: str = "home"
    history: list[str] = field(default_factory=list)
    font_size: int = 16
    spacing: int = 8
    high_contrast: bool = False
    closed: bool = False
    current_word: str = ""
    current_words: list[str] = field(default_factory=list)
    current_index: int = 0
    score: int = 0
    total: int = 0
    activity: str = ""
    feedback: str = ""
    submitted_answer: str = ""


class DashboardController:
    def __init__(self, speaker: Callable[[str], None] | None = None):
        self.state = DashboardState()
        self.speaker = speaker or coach.pronounce_word

    def home(self):
        self.state.history.append(self.state.screen)
        self.state.screen = "home"
        return self.menu_functions()

    def back(self):
        if self.state.history:
            self.state.screen = self.state.history.pop()
        return self.state.screen

    def increase_text(self): self.state.font_size += 2
    def decrease_text(self): self.state.font_size = max(10, self.state.font_size - 2)
    def increase_spacing(self): self.state.spacing += 4
    def decrease_spacing(self): self.state.spacing = max(0, self.state.spacing - 4)
    def toggle_high_contrast(self): self.state.high_contrast = not self.state.high_contrast
    def repeat_word(self):
        if self.state.current_word:
            self.speaker(self.state.current_word)

    def menu_functions(self) -> list[str]:
        return ["Practice All Words", "Spelling Test", "Add New Word", "Show Word List", "Practice Missed Words", "Show Missed Words", "Clear Missed Words", "Show Word Meanings", "Practice by Level", "Score History", "Exit Dashboard", "Internet Words", "Pending Internet Words", "Approve Internet Words", "Random Practice", "Progress Report", "Pronounce"]

    def start_practice(self, words: list[str], activity="Practice All Words"):
        self.state.history.append(self.state.screen); self.state.screen = "practice"
        self.state.current_words = [w.lower() for w in words if w]
        self.state.current_index = 0; self.state.score = 0; self.state.total = len(self.state.current_words); self.state.activity = activity; self.state.feedback = ""
        if self.state.current_words:
            self.state.current_word = self.state.current_words[0]; self.speaker(self.state.current_word)
        return self.prompt()

    def prompt(self) -> str:
        if not self.state.current_words: return "No words to practice."
        meanings = load_dashboard_meanings(); w = self.state.current_word
        return f"{self.state.activity}\nWord {self.state.current_index+1} of {self.state.total}\nMeaning: {meanings.get(w, NO_MEANING)}"

    def submit_answer(self, answer: str) -> str:
        word = self.state.current_word; self.state.submitted_answer = answer.strip().lower()
        if self.state.submitted_answer == word:
            self.state.score += 1; self.state.feedback = f"Correct! You spelled {word}."
        else:
            coach.save_missed_word(word); self.state.feedback = f"Not quite. Your answer: {answer}. Correct spelling: {word}."
        return self.state.feedback

    def next_word_or_finish(self) -> str:
        self.state.current_index += 1
        if self.state.current_index >= self.state.total:
            if self.state.total:
                save_score_with_activity(self.state.activity, self.state.score, self.state.total)
            self.state.screen = "complete"
            return f"Complete. Score: {self.state.score} out of {self.state.total}"
        self.state.current_word = self.state.current_words[self.state.current_index]; self.speaker(self.state.current_word); return self.prompt()

    def start_spelling_test(self, count_text: str):
        words = self.state.words.copy(); random.shuffle(words)
        if count_text.strip().lower() == "all":
            selected = words
        else:
            try: count = int(count_text)
            except ValueError: return "Please enter a number or all."
            if count < 1 or count > len(words): return f"Choose 1 to {len(words)}, or all."
            selected = words[:count]
        return self.start_practice(selected, "Spelling Test")

    def random_practice(self, group: str, amount_text: str):
        groups = {"all": self.state.words, **coach.LEVELS}
        if group not in groups: return "Please choose a valid Random Practice option."
        words = groups[group]
        try: amount = int(amount_text)
        except ValueError: return "Please enter a number."
        if amount < 1 or amount > min(5, len(words)): return f"Choose 1 to {min(5, len(words))}."
        return self.start_practice(random.sample(words, amount), "Random Practice")

    def practice_by_level(self, level: str):
        if level not in coach.LEVELS: return "Please choose a valid level."
        return self.start_practice(coach.LEVELS[level], f"Practice by Level: {level}")

    def practice_missed_words(self): return self.start_practice(coach.load_missed_words(), "Practice Missed Words")
    def show_word_list(self): self.state.screen="word_list"; return "\n".join(self.state.words) or "No words found."
    def show_meanings(self):
        meanings=load_dashboard_meanings(); return "\n".join(f"{w}: {meanings.get(w, NO_MEANING)}" for w in self.state.words)
    def show_missed_words(self): return "\n".join(coach.load_missed_words()) or "No missed words saved."
    def clear_missed_words(self, confirm: bool):
        if confirm: coach.clear_missed_words(); return "Missed words cleared."
        return "Missed words were not cleared."
    def add_new_word(self, word: str):
        clean = coach.clean_internet_word(word)
        if not clean: return "Please enter a valid word."
        if clean in self.state.words: return "That word is already in the list."
        self.state.words.append(clean); coach.save_words(self.state.words); return f"Added and saved word: {clean}"
    def pronounce(self, word: str):
        clean = word.strip()
        if not clean: return "No word to pronounce."
        self.speaker(clean); return f"Speaking: {clean}"
    def score_history(self):
        lines = _read_lines(coach.SCORE_HISTORY_FILE)
        if not lines: return "No scores saved yet."
        return "\n\n".join(f"Date/Time: {r['date']} {r['time']}\nActivity: {r['activity']}\n{r['score']}" for r in map(parse_score_record, lines))
    def internet_words(self, fetcher=None):
        if fetcher is None:
            return "Internet search is available in the terminal workflow; dashboard review-before-save connection is not configured for automated use yet."
        try: data = fetcher("computer")
        except (urllib.error.URLError, TimeoutError, OSError): return "Internet error. Check your connection and try again."
        return data
    def pending_internet_words(self): return "\n".join(_read_lines(coach.PENDING_WORDS_FILE)) or "No pending words yet."
    def approve_selected_pending(self, selected: list[int]):
        pending = _read_lines(coach.PENDING_WORDS_FILE); approved=[]; remaining=[]; existing=set(self.state.words)
        for i,line in enumerate(pending):
            if i in selected and "|" in line:
                word, meaning = line.split("|",1); word=coach.clean_internet_word(word)
                if word and word not in existing: approved.append((word, meaning.strip())); existing.add(word)
                else: remaining.append(line)
            else: remaining.append(line)
        if approved:
            self.state.words.extend(w for w,_ in approved); coach.save_words(self.state.words)
            with open(coach.MEANINGS_FILE,"a",encoding="utf-8") as f:
                for w,m in approved: f.write(f"{w}|{m}\n")
        with open(coach.PENDING_WORDS_FILE,"w",encoding="utf-8") as f: f.write("\n".join(remaining) + ("\n" if remaining else ""))
        return f"Approved {len(approved)} word(s)."
    def progress_report(self):
        return f"Total words: {len(self.state.words)}\nPending internet words: {len(_read_lines(coach.PENDING_WORDS_FILE))}\nMissed words to practice: {len(coach.load_missed_words())}\nSaved score records: {len(_read_lines(coach.SCORE_HISTORY_FILE))}"
    def exit_dashboard(self): self.state.closed=True; return "Dashboard closed."


class DashboardApp(tk.Tk):
    def __init__(self):
        super().__init__(); self.title("Derek's Reading & Spelling Coach"); self.controller=DashboardController(); self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.output = tk.Text(self, width=70, height=12, wrap="word")
        tk.Label(self, text="Derek's Reading & Spelling Coach", font=("Arial", 18, "bold")).pack(padx=16, pady=16)
        controls = tk.Frame(self); controls.pack()
        for label, command in [("A+", self.controller.increase_text), ("A-", self.controller.decrease_text), ("Space+", self.controller.increase_spacing), ("Space-", self.controller.decrease_spacing), ("High Contrast", self.controller.toggle_high_contrast), ("Home", self.controller.home), ("Back", self.controller.back)]:
            tk.Button(controls, text=label, command=lambda c=command: self.show(c())).pack(side="left", padx=4, pady=4)
        for name in self.controller.menu_functions():
            tk.Button(self, text=name, width=28, command=lambda n=name: self.run_menu_action(n)).pack(padx=12, pady=self.controller.state.spacing)
        self.output.pack(padx=12, pady=12, fill="both", expand=True)

    def show(self, text=None):
        if text is None:
            text = f"Screen: {self.controller.state.screen}"
        self.output.delete("1.0", "end"); self.output.insert("1.0", str(text))

    def run_menu_action(self, name: str):
        actions = {
            "Practice All Words": lambda: self.controller.start_practice(self.controller.state.words),
            "Spelling Test": lambda: self.controller.start_spelling_test("all"),
            "Add New Word": lambda: self.controller.add_new_word(simpledialog.askstring("Add New Word", "Enter a word to add:") or ""),
            "Show Word List": self.controller.show_word_list,
            "Practice Missed Words": self.controller.practice_missed_words,
            "Show Missed Words": self.controller.show_missed_words,
            "Clear Missed Words": lambda: self.controller.clear_missed_words(messagebox.askyesno("Clear missed words", "Clear all missed words?")),
            "Show Word Meanings": self.controller.show_meanings,
            "Practice by Level": lambda: self.controller.practice_by_level("easy"),
            "Score History": self.controller.score_history,
            "Exit Dashboard": self.destroy,
            "Internet Words": self.controller.internet_words,
            "Pending Internet Words": self.controller.pending_internet_words,
            "Approve Internet Words": self.approve_pending_dialog,
            "Random Practice": lambda: self.controller.random_practice("all", "1"),
            "Progress Report": self.controller.progress_report,
            "Pronounce": lambda: self.controller.pronounce(simpledialog.askstring("Pronounce", "Enter a word to pronounce:") or ""),
        }
        result = actions[name]()
        if name == "Exit Dashboard":
            return
        self.show(result)

    def approve_pending_dialog(self):
        pending = _read_lines(coach.PENDING_WORDS_FILE)
        if not pending:
            return "No pending words yet."
        choice = simpledialog.askstring("Approve Pending Words", "Enter item numbers to approve, separated by commas:") or ""
        selected = []
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit():
                selected.append(int(part) - 1)
        return self.controller.approve_selected_pending(selected)


def main():
    DashboardApp().mainloop()


if __name__ == "__main__":
    main()
