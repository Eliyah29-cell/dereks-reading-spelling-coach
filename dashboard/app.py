"""Tkinter Dashboard Prototype 1.

Run with: python -m dashboard.app
"""
import tkinter as tk
from tkinter import messagebox, ttk

import reading_spelling_coach as coach
from dashboard.logic import AutoScrollState, DashboardController, RandomPracticeSession, SpellingTestSession


class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Derek's Reading & Spelling Coach Dashboard")
        self.controller = DashboardController()
        self.auto_scroll = AutoScrollState()
        self.font_size = tk.IntVar(value=18)
        self.spacing = tk.IntVar(value=12)
        self.high_contrast = tk.BooleanVar(value=False)
        self.active_session = None
        self.answer_var = tk.StringVar()
        self.build_shell()
        self.show_home()

    def colors(self):
        if self.high_contrast.get():
            return {"bg": "#000000", "fg": "#ffffff", "card": "#1e1e1e", "button": "#ffd84d"}
        return {"bg": "#f7f4ea", "fg": "#1f2933", "card": "#ffffff", "button": "#dbeafe"}

    def build_shell(self):
        self.root.bind("<Control-h>", lambda event: self.show_home())
        self.root.bind("<Escape>", lambda event: self.show_home())
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Home", command=self.show_home).pack(side="left", padx=5)
        ttk.Button(top, text="Back", command=self.show_home).pack(side="left", padx=5)
        ttk.Button(top, text="A+", command=lambda: self.font_size.set(self.font_size.get() + 2) or self.refresh()).pack(side="right", padx=5)
        ttk.Button(top, text="A-", command=lambda: self.font_size.set(max(14, self.font_size.get() - 2)) or self.refresh()).pack(side="right", padx=5)
        ttk.Checkbutton(top, text="High contrast", variable=self.high_contrast, command=self.refresh).pack(side="right", padx=5)
        self.main = tk.Frame(self.root)
        self.main.pack(fill="both", expand=True)

    def clear(self):
        for child in self.main.winfo_children():
            child.destroy()
        c = self.colors()
        self.root.configure(bg=c["bg"])
        self.main.configure(bg=c["bg"])

    def refresh(self):
        if self.controller.active_activity:
            self.open_activity(self.controller.active_activity)
        else:
            self.show_home()

    def make_button(self, parent, text, command):
        c = self.colors()
        button = tk.Button(parent, text=text, command=command, font=("Arial", self.font_size.get()), bg=c["button"], fg="#000000", padx=18, pady=12, takefocus=True)
        button.pack(fill="x", pady=self.spacing.get() // 2)
        return button

    def heading(self, parent, text):
        c = self.colors()
        label = tk.Label(parent, text=text, font=("Arial", self.font_size.get() + 6, "bold"), bg=c["bg"], fg=c["fg"], anchor="w")
        label.pack(fill="x", pady=(self.spacing.get(), self.spacing.get() // 2))
        return label

    def show_home(self):
        self.controller.go_home()
        self.active_session = None
        self.clear()
        self.heading(self.main, "Dashboard Home")
        tk.Label(self.main, text="Choose one activity. The terminal app is still available separately.", font=("Arial", self.font_size.get()), bg=self.colors()["bg"], fg=self.colors()["fg"]).pack(anchor="w", padx=12)
        for group, controls in self.controller.home_model().items():
            frame = tk.LabelFrame(self.main, text=group, font=("Arial", self.font_size.get(), "bold"), padx=14, pady=14, bg=self.colors()["card"], fg=self.colors()["fg"]) 
            frame.pack(fill="x", padx=14, pady=10)
            for label, activity in controls.items():
                if activity == "home":
                    command = self.show_home
                elif activity == "exit":
                    command = self.root.destroy
                else:
                    command = lambda activity=activity: self.open_activity(activity)
                self.make_button(frame, label, command)

    def open_activity(self, activity):
        self.controller.open_activity(activity)
        if activity == "random_practice":
            self.show_random_menu()
        elif activity == "spelling_test":
            self.start_spelling_test()
        elif activity == "score_history":
            self.show_score_history()
        elif activity == "clear_missed_words":
            self.confirm_clear_missed_words()
        elif activity == "missed_words":
            self.show_lines("Missed Words", coach.load_missed_words() or ["No missed words saved."])
        elif activity == "word_list":
            self.show_lines("Word List", coach.load_words())
        elif activity == "word_meanings":
            meanings = coach.load_meanings()
            self.show_lines("Word Meanings", [f"{w}: {meanings.get(w, 'No meaning saved yet.')}" for w in coach.load_words()])
        else:
            self.show_placeholder(activity)

    def show_placeholder(self, activity):
        self.clear()
        self.heading(self.main, activity.replace("_", " ").title())
        tk.Label(self.main, text="This dashboard button is wired for Prototype 1. Some full workflows still use the terminal version.", font=("Arial", self.font_size.get()), wraplength=850, bg=self.colors()["bg"], fg=self.colors()["fg"]).pack(padx=14, pady=14)
        self.make_button(self.main, "Return Home", self.show_home)

    def show_lines(self, title, lines):
        self.clear()
        self.heading(self.main, title)
        box = tk.Text(self.main, font=("Arial", self.font_size.get()), wrap="word", height=15)
        box.pack(fill="both", expand=True, padx=14, pady=14)
        for line in lines:
            box.insert("end", str(line) + "\n")
        box.configure(state="disabled")
        self.make_button(self.main, "Return Home", self.show_home)

    def show_score_history(self):
        records = coach.load_score_records()
        lines = []
        for record in records:
            activity = record.activity or "Unlabeled activity"
            lines.append(f"{record.date_text} | {activity} | Score: {record.score} out of {record.total}")
        self.show_lines("Score History", lines or ["No scores saved yet."])

    def confirm_clear_missed_words(self):
        if messagebox.askyesno("Clear missed words?", "Clear all missed words? This cannot be undone."):
            coach.clear_missed_words()
            self.show_lines("Missed Words", ["Missed words cleared."])
        else:
            self.show_home()

    def show_random_menu(self):
        self.clear()
        self.heading(self.main, "Random Practice")
        options = [("All words", coach.load_words()), ("Easy", coach.LEVELS["easy"]), ("Medium", coach.LEVELS["medium"]), ("Hard", coach.LEVELS["hard"]), ("Cybersecurity", coach.LEVELS["cybersecurity"])]
        for label, words in options:
            self.make_button(self.main, label, lambda words=words: self.start_random(words))
        self.make_button(self.main, "Return to dashboard", self.show_home)

    def start_random(self, words):
        self.active_session = RandomPracticeSession(words[:1], coach.load_meanings(), coach.save_missed_word, coach.save_score, coach.pronounce_word)
        self.show_activity_prompt(self.active_session.start())

    def start_spelling_test(self):
        self.active_session = SpellingTestSession(coach.load_words()[:1], coach.save_missed_word, coach.save_score, coach.pronounce_word)
        self.show_activity_prompt(self.active_session.start())

    def show_activity_prompt(self, prompt):
        self.clear()
        self.auto_scroll.add_active_output()
        self.heading(self.main, self.active_session.activity_label)
        if self.auto_scroll.should_show_jump_control:
            self.make_button(self.main, "Jump to current question", lambda: self.auto_scroll.jump_to_current_question() or self.show_activity_prompt(prompt))
        text = prompt.instruction
        if prompt.word_visible and prompt.word:
            text += f"\n\nWord: {prompt.word}\nMeaning: {prompt.meaning}"
        tk.Label(self.main, text=text, font=("Arial", self.font_size.get()), justify="left", wraplength=850, bg=self.colors()["bg"], fg=self.colors()["fg"]).pack(anchor="w", padx=14, pady=14)
        self.make_button(self.main, "Repeat Word", self.active_session.repeat_word)
        entry = tk.Entry(self.main, textvariable=self.answer_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.submit_answer())
        self.make_button(self.main, "Submit", self.submit_answer)
        self.make_button(self.main, "Return Home", self.show_home)

    def submit_answer(self):
        feedback = self.active_session.submit_answer(self.answer_var.get())
        self.answer_var.set("")
        self.clear()
        self.auto_scroll.add_active_output()
        self.heading(self.main, "Feedback")
        tk.Label(self.main, text=feedback.message, font=("Arial", self.font_size.get()), wraplength=850, bg=self.colors()["bg"], fg=self.colors()["fg"]).pack(padx=14, pady=14)
        if feedback.finished:
            self.make_button(self.main, "Return Home", self.show_home)
        else:
            self.make_button(self.main, "Next Question", lambda: self.show_activity_prompt(self.active_session.start()))


def main():
    root = tk.Tk()
    root.geometry("900x700")
    DashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
