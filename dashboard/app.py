"""Tkinter Dashboard Prototype 1.

Run with: python -m dashboard.app
"""
import tkinter as tk
from tkinter import messagebox, ttk

import reading_spelling_coach as coach
from dashboard.logic import (
    AutoScrollState,
    DashboardController,
    RandomPracticeSession,
    SpellingTestSession,
    select_random_words,
)


class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Derek's Reading & Spelling Coach Dashboard")
        self.controller = DashboardController()
        self.auto_scroll = AutoScrollState()
        self.font_size = tk.IntVar(value=self.controller.display_settings.font_size)
        self.spacing = tk.IntVar(value=self.controller.display_settings.spacing)
        self.high_contrast = tk.BooleanVar(value=self.controller.display_settings.high_contrast)
        self.active_session = None
        self.current_prompt = None
        self.current_view = "home"
        self.random_group_words: list[str] = []
        self.answer_var = tk.StringVar()
        self.amount_var = tk.StringVar(value="1")
        self.build_shell()
        self.show_home()

    def colors(self):
        if self.high_contrast.get():
            return {"bg": "#000000", "fg": "#ffffff", "card": "#1e1e1e", "button": "#ffd84d", "disabled": "#555555"}
        return {"bg": "#f7f4ea", "fg": "#1f2933", "card": "#ffffff", "button": "#dbeafe", "disabled": "#e5e7eb"}

    def build_shell(self):
        self.root.bind("<Control-h>", lambda event: self.show_home())
        self.root.bind("<Escape>", lambda event: self.go_back())
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Home", command=self.show_home).pack(side="left", padx=5)
        ttk.Button(top, text="Back", command=self.go_back).pack(side="left", padx=5)
        ttk.Button(top, text="A+", command=self.increase_font).pack(side="right", padx=5)
        ttk.Button(top, text="A-", command=self.decrease_font).pack(side="right", padx=5)
        ttk.Button(top, text="Space+", command=self.increase_spacing).pack(side="right", padx=5)
        ttk.Button(top, text="Space-", command=self.decrease_spacing).pack(side="right", padx=5)
        ttk.Checkbutton(top, text="High contrast", variable=self.high_contrast, command=self.update_accessibility).pack(side="right", padx=5)

        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.main = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.main.bind("<Configure>", self.update_scroll_region)
        self.canvas.bind("<Configure>", self.resize_canvas_window)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_linux_scroll_up)
        self.canvas.bind_all("<Button-5>", self.on_linux_scroll_down)
        for key in ["<Prior>", "<Next>", "<Home>", "<End>"]:
            self.root.bind(key, self.on_keyboard_scroll)

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def resize_canvas_window(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        if event.delta > 0:
            self.auto_scroll.manual_scroll_up()
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_linux_scroll_up(self, event):
        self.auto_scroll.manual_scroll_up()
        self.canvas.yview_scroll(-3, "units")

    def on_linux_scroll_down(self, event):
        self.canvas.yview_scroll(3, "units")

    def on_keyboard_scroll(self, event):
        if event.keysym in ["Prior", "Home"]:
            self.auto_scroll.manual_scroll_up()
        if event.keysym == "Prior":
            self.canvas.yview_scroll(-1, "pages")
        elif event.keysym == "Next":
            self.canvas.yview_scroll(1, "pages")
        elif event.keysym == "Home":
            self.canvas.yview_moveto(0)
        elif event.keysym == "End":
            self.canvas.yview_moveto(1)

    def scroll_to_active_if_requested(self):
        if self.auto_scroll.scroll_to_active_requested:
            self.root.after_idle(lambda: self.canvas.yview_moveto(1.0))
            self.auto_scroll.mark_scrolled_to_active()

    def update_accessibility(self):
        self.controller.update_display_settings(self.font_size.get(), self.spacing.get(), self.high_contrast.get())
        self.render_current_view()

    def increase_font(self):
        self.font_size.set(self.font_size.get() + 2)
        self.update_accessibility()

    def decrease_font(self):
        self.font_size.set(max(14, self.font_size.get() - 2))
        self.update_accessibility()

    def increase_spacing(self):
        self.spacing.set(min(32, self.spacing.get() + 2))
        self.update_accessibility()

    def decrease_spacing(self):
        self.spacing.set(max(6, self.spacing.get() - 2))
        self.update_accessibility()

    def clear(self):
        for child in self.main.winfo_children():
            child.destroy()
        c = self.colors()
        self.root.configure(bg=c["bg"])
        self.canvas.configure(bg=c["bg"])
        self.main.configure(bg=c["bg"])

    def make_button(self, parent, text, command, enabled=True):
        c = self.colors()
        button = tk.Button(
            parent,
            text=text,
            command=command if enabled else None,
            font=("Arial", self.font_size.get()),
            bg=c["button"] if enabled else c["disabled"],
            fg="#000000",
            padx=18,
            pady=12,
            takefocus=enabled,
            state="normal" if enabled else "disabled",
        )
        button.pack(fill="x", pady=self.spacing.get() // 2)
        return button

    def heading(self, parent, text):
        c = self.colors()
        label = tk.Label(parent, text=text, font=("Arial", self.font_size.get() + 6, "bold"), bg=c["bg"], fg=c["fg"], anchor="w")
        label.pack(fill="x", pady=(self.spacing.get(), self.spacing.get() // 2))
        return label

    def body_text(self, parent, text):
        c = self.colors()
        label = tk.Label(parent, text=text, font=("Arial", self.font_size.get()), justify="left", wraplength=850, bg=c["bg"], fg=c["fg"])
        label.pack(anchor="w", padx=14, pady=self.spacing.get())
        return label

    def show_home(self):
        self.controller.go_home()
        self.current_view = "home"
        self.clear()
        self.heading(self.main, "Dashboard Home")
        self.body_text(self.main, "Choose one Prototype 1 activity. Unfinished controls are disabled and labeled clearly.")
        for group, controls in self.controller.home_model().items():
            frame = tk.LabelFrame(self.main, text=group, font=("Arial", self.font_size.get(), "bold"), padx=14, pady=14, bg=self.colors()["card"], fg=self.colors()["fg"])
            frame.pack(fill="x", padx=14, pady=10)
            for label, activity in controls.items():
                enabled = self.controller.is_functional(activity)
                text = label if enabled else f"{label} — Not available in Prototype 1"
                if activity == "home":
                    command = self.show_home
                elif activity == "exit":
                    command = self.root.destroy
                else:
                    command = lambda activity=activity: self.open_activity(activity)
                self.make_button(frame, text, command, enabled=enabled)
        self.canvas.yview_moveto(0)

    def render_current_view(self):
        answer_text = self.answer_var.get()
        amount_text = self.amount_var.get()
        if self.current_view == "home":
            self.show_home()
        elif self.current_view == "random_menu":
            self.show_random_menu(push=False)
        elif self.current_view == "random_amount":
            self.show_random_amount(push=False)
        elif self.current_view == "activity_prompt" and self.current_prompt:
            self.show_activity_prompt(self.current_prompt, push=False)
        elif self.current_view == "score_history":
            self.show_score_history(push=False)
        elif self.current_view == "lines":
            self.open_activity(self.controller.active_activity or "word_list", push=False)
        else:
            self.show_home()
        self.answer_var.set(answer_text)
        self.amount_var.set(amount_text)

    def go_back(self):
        previous = self.controller.back()
        if previous == "home":
            self.show_home()
        elif previous == "random_menu":
            self.show_random_menu(push=False)
        elif previous == "random_amount":
            self.show_random_amount(push=False)
        else:
            self.show_home()

    def open_activity(self, activity, push=True):
        if not self.controller.is_functional(activity):
            return
        self.controller.open_activity(activity)
        if activity == "random_practice":
            self.show_random_menu(push=push)
        elif activity == "spelling_test":
            self.start_spelling_test(push=push)
        elif activity == "score_history":
            self.show_score_history(push=push)
        elif activity == "clear_missed_words":
            self.confirm_clear_missed_words()
        elif activity == "missed_words":
            self.show_lines("Missed Words", coach.load_missed_words() or ["No missed words saved."], push=push)
        elif activity == "word_list":
            self.show_lines("Word List", coach.load_words(), push=push)
        elif activity == "word_meanings":
            meanings = coach.load_meanings()
            self.show_lines("Word Meanings", [f"{w}: {meanings.get(w, 'No meaning saved yet.')}" for w in coach.load_words()], push=push)
        elif activity == "exit":
            self.root.destroy()

    def show_lines(self, title, lines, push=True):
        if push:
            self.controller.push_screen("lines")
        self.current_view = "lines"
        self.clear()
        self.heading(self.main, title)
        box = tk.Text(self.main, font=("Arial", self.font_size.get()), wrap="word", height=15)
        box.pack(fill="both", expand=True, padx=14, pady=14)
        for line in lines:
            box.insert("end", str(line) + "\n")
        box.configure(state="disabled")
        self.make_button(self.main, "Return Home", self.show_home)
        self.canvas.yview_moveto(0)

    def show_score_history(self, push=True):
        if push:
            self.controller.push_screen("score_history")
        self.current_view = "score_history"
        records = coach.load_score_records()
        lines = []
        for record in records:
            activity = record.activity or "Unlabeled activity"
            lines.append(f"{record.date_text} | {activity} | Score: {record.score} out of {record.total}")
        self.show_lines("Score History", lines or ["No scores saved yet."], push=False)
        self.current_view = "score_history"

    def confirm_clear_missed_words(self):
        if messagebox.askyesno("Clear missed words?", "Clear all missed words? This cannot be undone."):
            coach.clear_missed_words()
            self.show_lines("Missed Words", ["Missed words cleared."])
        else:
            self.show_home()

    def show_random_menu(self, push=True):
        if push:
            self.controller.push_screen("random_menu")
        self.current_view = "random_menu"
        self.clear()
        self.heading(self.main, "Random Practice")
        options = [
            ("All words", coach.load_words()),
            ("Easy", coach.LEVELS["easy"]),
            ("Medium", coach.LEVELS["medium"]),
            ("Hard", coach.LEVELS["hard"]),
            ("Cybersecurity", coach.LEVELS["cybersecurity"]),
        ]
        for label, words in options:
            self.make_button(self.main, label, lambda words=words: self.choose_random_group(words))
        self.make_button(self.main, "Return to dashboard", self.show_home)
        self.canvas.yview_moveto(0)

    def choose_random_group(self, words):
        self.random_group_words = list(words)
        self.amount_var.set("1")
        self.show_random_amount(push=True)

    def show_random_amount(self, push=True):
        if push:
            self.controller.push_screen("random_amount")
        self.current_view = "random_amount"
        max_words = len(self.random_group_words)
        self.clear()
        self.heading(self.main, "How many words?")
        self.body_text(self.main, f"Choose 1 through {max_words}. Choose 1 for quick testing or more for normal practice.")
        entry = tk.Entry(self.main, textvariable=self.amount_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.start_random_from_amount())
        self.make_button(self.main, "Start Random Practice", self.start_random_from_amount, enabled=max_words > 0)
        self.make_button(self.main, "Back to Random Practice choices", lambda: self.show_random_menu(push=False))

    def start_random_from_amount(self):
        try:
            amount = int(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Choose a number", "Please enter a number.")
            return
        selected_words = select_random_words(self.random_group_words, amount)
        self.active_session = RandomPracticeSession(selected_words, coach.load_meanings(), coach.save_missed_word, coach.save_score, coach.pronounce_word)
        self.controller.push_screen("activity_prompt")
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=False)

    def start_spelling_test(self, push=True):
        if push:
            self.controller.push_screen("activity_prompt")
        self.active_session = SpellingTestSession(coach.load_words(), coach.save_missed_word, coach.save_score, coach.pronounce_word)
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=False)

    def show_activity_prompt(self, prompt, push=True):
        if push:
            self.controller.push_screen("activity_prompt")
        self.current_view = "activity_prompt"
        self.current_prompt = prompt
        self.clear()
        self.auto_scroll.add_active_output()
        self.heading(self.main, self.active_session.activity_label)
        if self.auto_scroll.should_show_jump_control:
            self.make_button(self.main, "Jump to current question", self.jump_to_current_question)
        progress = f"Question {prompt.question_number} of {prompt.total_questions}"
        text = f"{progress}\n{prompt.instruction}"
        if prompt.word_visible and prompt.word:
            text += f"\n\nWord: {prompt.word}\nMeaning: {prompt.meaning}"
        self.body_text(self.main, text)
        self.make_button(self.main, "Repeat Word", self.active_session.repeat_word)
        entry = tk.Entry(self.main, textvariable=self.answer_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.submit_answer())
        self.make_button(self.main, "Submit", self.submit_answer)
        self.make_button(self.main, "Return Home", self.show_home)
        self.scroll_to_active_if_requested()

    def jump_to_current_question(self):
        self.auto_scroll.jump_to_current_question()
        self.canvas.yview_moveto(1.0)
        if self.current_prompt:
            self.show_activity_prompt(self.current_prompt, push=False)

    def submit_answer(self):
        feedback = self.active_session.submit_answer(self.answer_var.get())
        self.answer_var.set("")
        self.clear()
        self.auto_scroll.add_active_output()
        self.heading(self.main, "Feedback")
        self.body_text(self.main, f"Question {feedback.question_number} of {feedback.total_questions}\n{feedback.message}")
        if feedback.finished:
            self.body_text(self.main, f"Activity complete. Score: {self.active_session.score} out of {self.active_session.answered_count}")
            self.make_button(self.main, "Return Home", self.show_home)
        else:
            self.make_button(self.main, "Next Question", self.next_question)
        self.scroll_to_active_if_requested()

    def next_question(self):
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=False)


def main():
    root = tk.Tk()
    root.geometry("900x700")
    DashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
