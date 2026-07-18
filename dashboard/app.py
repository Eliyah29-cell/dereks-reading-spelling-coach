"""Tkinter Dashboard Prototype 1.

Run with: python -m dashboard.app
"""
import tkinter as tk
from tkinter import messagebox, ttk

import reading_spelling_coach as coach
from dashboard.logic import (
    AutoScrollEventController,
    AutoScrollState,
    DashboardController,
    PracticeWordsSession,
    RandomPracticeSession,
    SpellingTestSession,
    prepare_spelling_test_words,
    select_random_words,
    validate_random_practice_amount,
    validate_spelling_test_amount,
)


class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Derek's Reading & Spelling Coach Dashboard")
        self.controller = DashboardController()
        self.auto_scroll = AutoScrollState()
        self.scroll_events = AutoScrollEventController(self.auto_scroll)
        self.font_size = tk.IntVar(value=self.controller.display_settings.font_size)
        self.spacing = tk.IntVar(value=self.controller.display_settings.spacing)
        self.high_contrast = tk.BooleanVar(value=self.controller.display_settings.high_contrast)
        self.active_session = None
        self.current_prompt = None
        self.current_view = "home"
        self.random_group_words: list[str] = []
        self.spelling_test_words: list[str] = []
        self.answer_var = tk.StringVar()
        self.amount_var = tk.StringVar(value="1")
        self.word_var = tk.StringVar()
        self.meaning_var = tk.StringVar()
        self.topic_var = tk.StringVar()
        self.internet_suggestions: list[tuple[str, str]] = []
        self.internet_selection_vars: list[tuple[tk.BooleanVar, str, str]] = []
        self.pending_selection_vars = []
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
        self.jump_button = ttk.Button(top, text="Jump to current question", command=self.jump_to_current_question)

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
        self.scrollbar.bind("<ButtonPress-1>", self.remember_scrollbar_position)
        self.scrollbar.bind("<B1-Motion>", self.on_scrollbar_drag)
        self.last_scrollbar_fraction = 0.0
        for key in ["<Prior>", "<Next>", "<Home>", "<End>"]:
            self.root.bind(key, self.on_keyboard_scroll)

    def update_scroll_region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def resize_canvas_window(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def on_mousewheel(self, event):
        self.scroll_events.mouse_wheel(event.delta, self.current_view in ["activity_prompt", "feedback"])
        self.update_jump_control_visibility()
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        if event.delta < 0:
            self.root.after_idle(self.maybe_resume_at_bottom)

    def on_linux_scroll_up(self, event):
        self.scroll_events.linux_button_4(self.current_view in ["activity_prompt", "feedback"])
        self.update_jump_control_visibility()
        self.canvas.yview_scroll(-3, "units")

    def on_linux_scroll_down(self, event):
        self.canvas.yview_scroll(3, "units")
        self.root.after_idle(self.maybe_resume_at_bottom)

    def remember_scrollbar_position(self, event):
        self.last_scrollbar_fraction = self.canvas.yview()[0]

    def on_scrollbar_drag(self, event):
        current_fraction = self.canvas.yview()[0]
        self.scroll_events.scrollbar_drag(self.last_scrollbar_fraction, current_fraction, self.current_view in ["activity_prompt", "feedback"])
        self.update_jump_control_visibility()
        if current_fraction > self.last_scrollbar_fraction:
            self.root.after_idle(self.maybe_resume_at_bottom)
        self.last_scrollbar_fraction = current_fraction

    def pause_auto_scroll_for_manual_review(self):
        if self.current_view in ["activity_prompt", "feedback"]:
            self.auto_scroll.manual_scroll_up()
            self.update_jump_control_visibility()

    def update_jump_control_visibility(self):
        if self.auto_scroll.should_show_jump_control and self.current_view in ["activity_prompt", "feedback"]:
            if not self.jump_button.winfo_ismapped():
                self.jump_button.pack(side="left", padx=5)
        else:
            if self.jump_button.winfo_ismapped():
                self.jump_button.pack_forget()

    def on_keyboard_scroll(self, event):
        self.scroll_events.keyboard_scroll(event.keysym, self.current_view in ["activity_prompt", "feedback"])
        self.update_jump_control_visibility()
        if event.keysym == "Prior":
            self.canvas.yview_scroll(-1, "pages")
        elif event.keysym == "Next":
            self.canvas.yview_scroll(1, "pages")
            self.root.after_idle(self.maybe_resume_at_bottom)
        elif event.keysym == "Home":
            self.canvas.yview_moveto(0)
        elif event.keysym == "End":
            self.canvas.yview_moveto(1)
            self.root.after_idle(self.maybe_resume_at_bottom)

    def scroll_to_active_if_requested(self):
        if self.auto_scroll.scroll_to_active_requested:
            self.root.after_idle(lambda: self.canvas.yview_moveto(1.0))
            self.auto_scroll.mark_scrolled_to_active()
            self.update_jump_control_visibility()

    def maybe_resume_at_bottom(self):
        bottom_fraction = self.canvas.yview()[1]
        if bottom_fraction >= 0.99:
            self.auto_scroll.manual_scroll_to_bottom()
            self.update_jump_control_visibility()

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
        self.auto_scroll.reset_for_new_activity()
        self.update_jump_control_visibility()
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
        word_text = self.word_var.get()
        meaning_text = self.meaning_var.get()
        topic_text = self.topic_var.get()
        internet_selected = {
            word for selected, word, meaning in self.internet_selection_vars if selected.get()
        }
        pending_selected = {
            self.pending_selection_key(selection)
            for selection in getattr(self, "pending_selection_vars", [])
            if selection[0].get()
        }
        if self.current_view == "home":
            self.show_home()
        elif self.current_view == "random_menu":
            self.show_random_menu(push=False)
        elif self.current_view == "random_amount":
            self.show_random_amount(push=False)
        elif self.current_view == "spelling_amount":
            self.show_spelling_amount(push=False)
        elif self.current_view == "add_word":
            self.show_add_word(push=False)
        elif self.current_view == "pronounce_word":
            self.show_pronounce_word(push=False)
        elif self.current_view == "internet_search":
            self.show_internet_words(push=False)
        elif self.current_view == "internet_review":
            self.show_internet_suggestions_for_review(self.internet_suggestions, push=False, selected_words=internet_selected)
        elif self.current_view == "practice_by_level":
            self.show_practice_by_level(push=False)
        elif self.current_view == "approve_pending_words":
            self.show_approve_pending_words(push=False, selected_keys=pending_selected)
        elif self.current_view == "activity_prompt" and self.current_prompt:
            self.show_activity_prompt(self.current_prompt, push=False, add_to_history=False)
        elif self.current_view == "feedback" and self.controller.current_feedback:
            self.show_feedback(self.controller.current_feedback, push=False, add_to_history=False)
        elif self.current_view == "score_history":
            self.show_score_history(push=False)
        elif self.current_view == "pending_words":
            self.show_pending_words(push=False)
        elif self.current_view == "progress_report":
            self.show_progress_report(push=False)
        elif self.current_view == "lines":
            self.open_activity(self.controller.active_activity or "word_list", push=False)
        else:
            self.show_home()
        self.answer_var.set(answer_text)
        self.amount_var.set(amount_text)
        self.word_var.set(word_text)
        self.meaning_var.set(meaning_text)
        self.topic_var.set(topic_text)

    def go_back(self):
        if self.current_view == "feedback" and self.controller.current_feedback:
            self.show_feedback(self.controller.current_feedback, push=False, add_to_history=False)
            return
        previous = self.controller.back()
        if previous == "home":
            self.show_home()
        elif previous == "random_menu":
            self.show_random_menu(push=False)
        elif previous == "random_amount":
            self.show_random_amount(push=False)
        elif previous == "spelling_amount":
            self.show_spelling_amount(push=False)
        elif previous == "activity_prompt" and self.current_prompt:
            self.show_activity_prompt(self.current_prompt, push=False, add_to_history=False)
        elif previous == "feedback" and self.controller.current_feedback:
            self.show_feedback(self.controller.current_feedback, push=False, add_to_history=False)
        elif previous == "add_word":
            self.show_add_word(push=False)
        elif previous == "pronounce_word":
            self.show_pronounce_word(push=False)
        elif previous == "internet_search":
            self.show_internet_words(push=False)
        elif previous == "internet_review":
            self.show_internet_suggestions_for_review(self.internet_suggestions, push=False)
        elif previous == "practice_by_level":
            self.show_practice_by_level(push=False)
        elif previous == "approve_pending_words":
            self.show_approve_pending_words(push=False)
        else:
            self.show_home()

    def open_activity(self, activity, push=True):
        if not self.controller.is_functional(activity):
            return
        self.controller.open_activity(activity)
        if activity == "random_practice":
            self.show_random_menu(push=push)
        elif activity == "practice_all_words":
            self.start_practice_words(coach.load_words(), "Practice All Words", push=push)
        elif activity == "practice_by_level":
            self.show_practice_by_level(push=push)
        elif activity == "practice_missed_words":
            self.start_practice_words(coach.load_missed_words(), "Practice Missed Words", push=push)
        elif activity == "spelling_test":
            self.show_spelling_amount(push=push)
        elif activity == "add_word":
            self.show_add_word(push=push)
        elif activity == "pronounce_word":
            self.show_pronounce_word(push=push)
        elif activity == "internet_words":
            self.show_internet_words(push=push)
        elif activity == "pending_words":
            self.show_pending_words(push=push)
        elif activity == "approve_pending_words":
            self.show_approve_pending_words(push=push)
        elif activity == "score_history":
            self.show_score_history(push=push)
        elif activity == "progress_report":
            self.show_progress_report(push=push)
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

    def start_practice_words(self, words, label, push=True):
        if push:
            self.controller.push_screen("activity_prompt")
        self.auto_scroll.reset_for_new_activity()
        self.controller.start_activity_history()
        self.active_session = PracticeWordsSession(list(words), coach.load_meanings(), coach.save_missed_word, coach.save_score, coach.pronounce_word, label)
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=False, add_to_history=True)

    def start_practice_level(self, level_name, words):
        label = f"Practice by Level: {level_name.title()}"
        self.start_practice_words(words, label, push=True)

    def show_lines(self, title, lines, push=True):
        if push:
            self.controller.push_screen("lines")
        else:
            self.controller.replace_screen("lines")
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
        else:
            self.controller.replace_screen("score_history")
        self.current_view = "score_history"
        records = coach.load_score_records()
        lines = []
        for record in records:
            activity = record.activity or "Unlabeled activity"
            lines.append(f"{record.date_text} | {activity} | Score: {record.score} out of {record.total}")
        self.show_lines("Score History", lines or ["No scores saved yet."], push=False)
        self.current_view = "score_history"
        self.controller.replace_screen("score_history")

    def show_progress_report(self, push=True):
        if push:
            self.controller.push_screen("lines")
        else:
            self.controller.replace_screen("progress_report")
        words = coach.load_words()
        meanings = coach.load_meanings()
        missed = coach.load_missed_words()
        pending = self.load_pending_word_pairs()
        records = coach.load_score_records()
        lines = [
            f"Total words: {len(words)}",
            f"Total meanings: {len(meanings)}",
            f"Pending internet words: {len(pending)}",
            f"Missed words to practice: {len(missed)}",
            f"Saved score records: {len(records)}",
        ]
        if records:
            percentages = coach.calculate_score_percentages(records)
            lines.append(f"Latest score: {records[-1].score} out of {records[-1].total}")
            lines.append(f"Best score percent: {max(percentages):.1f}%")
            lines.append(f"Average score percent: {sum(percentages) / len(percentages):.1f}%")
        self.show_lines("Progress Report", lines, push=False)
        self.current_view = "progress_report"
        self.controller.replace_screen("progress_report")

    def show_pending_words(self, push=True):
        if push:
            self.controller.push_screen("pending_words")
        else:
            self.controller.replace_screen("pending_words")
        pairs = self.load_pending_word_pairs()
        lines = [f"{word}: {meaning}" for word, meaning in pairs] or ["No pending words yet."]
        self.show_lines("Pending Internet Words", lines, push=False)
        self.current_view = "pending_words"
        self.controller.replace_screen("pending_words")

    def load_pending_word_pairs(self):
        return [(word, meaning) for word, meaning, raw_line in self.load_pending_word_records()]

    def load_pending_word_records(self):
        try:
            with open(coach.PENDING_WORDS_FILE, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            return []
        records = []
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if "|" in stripped_line:
                word, meaning = stripped_line.split("|", 1)
            else:
                word, meaning = stripped_line, "No meaning found yet."
            word = coach.clean_internet_word(word)
            if word:
                records.append((word, meaning.strip(), line))
        return records

    def confirm_clear_missed_words(self):
        if messagebox.askyesno("Clear missed words?", "Clear all missed words? This cannot be undone."):
            coach.clear_missed_words()
            self.show_lines("Missed Words", ["Missed words cleared."])
        else:
            self.show_home()

    def show_random_menu(self, push=True):
        if push:
            self.controller.push_screen("random_menu")
        else:
            self.controller.replace_screen("random_menu")
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

    def show_practice_by_level(self, push=True):
        if push:
            self.controller.push_screen("practice_by_level")
        else:
            self.controller.replace_screen("practice_by_level")
        self.current_view = "practice_by_level"
        self.clear()
        self.heading(self.main, "Practice by Level")
        self.body_text(self.main, "Choose one existing level. The practice session will use that level's words.")
        for level_name, words in coach.LEVELS.items():
            label = f"{level_name.title()} ({len(words)} words)"
            self.make_button(self.main, label, lambda level_name=level_name, words=words: self.start_practice_level(level_name, words), enabled=bool(words))
        self.make_button(self.main, "Return to dashboard", self.show_home)
        self.canvas.yview_moveto(0)

    def choose_random_group(self, words):
        self.random_group_words = list(words)
        self.amount_var.set("1")
        self.controller.replace_screen("random_menu")
        self.show_random_amount(push=True)

    def show_random_amount(self, push=True):
        if push:
            self.controller.push_screen("random_amount")
        else:
            self.controller.replace_screen("random_amount")
        self.current_view = "random_amount"
        max_words = min(len(self.random_group_words), 5)
        self.clear()
        self.heading(self.main, "How many words?")
        self.body_text(self.main, f"Choose 1 through {max_words}. Random Practice is limited to 5 words at a time.")
        entry = tk.Entry(self.main, textvariable=self.amount_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.start_random_from_amount())
        self.make_button(self.main, "Start Random Practice", self.start_random_from_amount, enabled=max_words > 0)
        self.make_button(self.main, "Back to Random Practice choices", self.back_to_random_choices)

    def show_spelling_amount(self, push=True):
        if push:
            self.controller.push_screen("spelling_amount")
        else:
            self.controller.replace_screen("spelling_amount")
        self.current_view = "spelling_amount"
        self.spelling_test_words = prepare_spelling_test_words(coach.load_words())
        max_words = len(self.spelling_test_words)
        self.clear()
        self.heading(self.main, "Spelling Test")
        self.body_text(self.main, f"Choose a word count from 1 through {max_words}, or type all for every word.")
        entry = tk.Entry(self.main, textvariable=self.amount_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.bind("<Return>", lambda event: self.start_spelling_test_from_amount())
        self.make_button(self.main, "Start Spelling Test", self.start_spelling_test_from_amount, enabled=max_words > 0)
        self.make_button(self.main, "Return Home", self.show_home)

    def start_spelling_test_from_amount(self):
        valid, amount, message = validate_spelling_test_amount(self.amount_var.get(), len(self.spelling_test_words))
        if not valid:
            messagebox.showerror("Choose a number", message)
            return
        selected_words = self.spelling_test_words[:amount]
        self.start_spelling_test(selected_words, push=True)

    def show_add_word(self, push=True):
        if push:
            self.controller.push_screen("add_word")
        else:
            self.controller.replace_screen("add_word")
        self.current_view = "add_word"
        self.clear()
        self.heading(self.main, "Add New Word")
        self.body_text(self.main, "Type one new practice word and an optional meaning.")
        tk.Entry(self.main, textvariable=self.word_var, font=("Arial", self.font_size.get())).pack(fill="x", padx=14, pady=8, ipady=8)
        tk.Entry(self.main, textvariable=self.meaning_var, font=("Arial", self.font_size.get())).pack(fill="x", padx=14, pady=8, ipady=8)
        self.make_button(self.main, "Save Word", self.save_new_word)
        self.make_button(self.main, "Return Home", self.show_home)

    def save_new_word(self):
        word = coach.clean_internet_word(self.word_var.get())
        if not word:
            messagebox.showerror("Word needed", "Please enter a word using letters or hyphens.")
            return
        words = coach.load_words()
        if word not in words:
            words.append(word)
            coach.save_words(words)
        meaning = self.meaning_var.get().strip()
        if meaning:
            self.append_or_update_meaning_line(word, meaning)
        self.show_lines("Add New Word", [f"Saved word: {word}"], push=False)

    def show_pronounce_word(self, push=True):
        if push:
            self.controller.push_screen("pronounce_word")
        else:
            self.controller.replace_screen("pronounce_word")
        self.current_view = "pronounce_word"
        self.clear()
        self.heading(self.main, "Pronounce")
        tk.Entry(self.main, textvariable=self.word_var, font=("Arial", self.font_size.get())).pack(fill="x", padx=14, pady=14, ipady=8)
        self.make_button(self.main, "Pronounce Word", self.pronounce_entered_word)
        self.make_button(self.main, "Return Home", self.show_home)

    def pronounce_entered_word(self):
        word = self.word_var.get().strip()
        if word:
            coach.pronounce_word(word)

    def show_internet_words(self, push=True):
        if push:
            self.controller.push_screen("internet_search")
        else:
            self.controller.replace_screen("internet_search")
        self.current_view = "internet_search"
        self.clear()
        self.heading(self.main, "Internet Words Review Before Save")
        self.body_text(self.main, "Enter a topic. Suggestions will be shown for review before anything is saved.")
        entry = tk.Entry(self.main, textvariable=self.topic_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.bind("<Return>", lambda event: self.fetch_internet_words_for_review())
        self.make_button(self.main, "Find Internet Words", self.fetch_internet_words_for_review)
        self.make_button(self.main, "Return Home", self.show_home)

    def fetch_internet_words_for_review(self):
        topic = self.topic_var.get().strip()
        suggestions, error_message = self.fetch_internet_suggestions(topic)
        if error_message:
            self.show_lines("Internet Words Review Before Save", [error_message], push=False)
            self.current_view = "internet_search"
            self.controller.replace_screen("internet_search")
            return
        self.show_internet_suggestions_for_review(suggestions, push=False)

    def fetch_internet_suggestions(self, topic):
        search_topic = coach.prepare_internet_search_topic(topic)
        if not search_topic:
            return [], "Please enter a search topic."
        safe_topic = coach.urllib.parse.quote(search_topic)
        url = f"https://api.datamuse.com/words?ml={safe_topic}&md=d&max=30"
        try:
            with coach.urllib.request.urlopen(url, timeout=10) as response:
                data = coach.json.loads(response.read().decode("utf-8"))
        except (coach.urllib.error.URLError, TimeoutError):
            return [], "Internet connection failed safely. No words were saved."
        except (UnicodeDecodeError, coach.json.JSONDecodeError):
            return [], "Internet response could not be read safely. No words were saved."
        if not isinstance(data, list):
            return [], "Internet response had an unexpected format. No words were saved."
        current_words = coach.load_word_set(coach.WORDS_FILE)
        pending_words = coach.load_word_set(coach.PENDING_WORDS_FILE)
        suggestions = []
        for item in data:
            if not isinstance(item, dict):
                continue
            word = coach.clean_internet_word(item.get("word", ""))
            if not word or word in current_words or word in pending_words:
                continue
            definitions = item.get("defs", [])
            meaning = coach.clean_definition(definitions[0]) if definitions else "No meaning found yet."
            if meaning == "No meaning found yet.":
                meaning = coach.load_meanings().get(word, meaning)
            if coach.word_matches_search_topic(word, meaning, search_topic) and coach.word_matches_difficulty(word, meaning, "mixed"):
                suggestions.append((word, meaning))
        return suggestions, ""

    def show_internet_suggestions_for_review(self, suggestions, push=True, selected_words=None):
        if push:
            self.controller.push_screen("internet_review")
        else:
            self.controller.replace_screen("internet_review")
        self.current_view = "internet_review"
        if selected_words is None:
            selected_words = set()
        self.internet_suggestions = suggestions
        self.internet_selection_vars = []
        self.clear()
        self.heading(self.main, "Review Internet Word Suggestions")
        if not suggestions:
            self.body_text(self.main, "No usable suggestions were found. Try another topic.")
        for word, meaning in suggestions:
            selected = tk.BooleanVar(value=word in selected_words)
            self.internet_selection_vars.append((selected, word, meaning))
            tk.Checkbutton(self.main, text=f"{word}: {meaning}", variable=selected, font=("Arial", self.font_size.get()), bg=self.colors()["bg"], fg=self.colors()["fg"]).pack(anchor="w", padx=14, pady=4)
        self.make_button(self.main, "Save Selected to Pending Words", self.save_selected_internet_words, enabled=bool(suggestions))
        self.make_button(self.main, "Return Home", self.show_home)

    def save_selected_internet_words(self):
        selected = [(word, meaning) for var, word, meaning in self.internet_selection_vars if var.get()]
        if not selected:
            messagebox.showerror("Choose words", "Select at least one suggested word to save.")
            return
        with open(coach.PENDING_WORDS_FILE, "a") as file:
            for word, meaning in selected:
                file.write(f"{word}|{meaning}\n")
        self.show_lines("Internet Words Review Before Save", [f"Saved {len(selected)} selected word(s) to pending words."], push=False)

    def append_or_update_meaning_line(self, word, meaning):
        try:
            with open(coach.MEANINGS_FILE, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []
        replacement = f"{word}|{meaning.strip()}\n"
        updated = False
        output_lines = []
        for line in lines:
            if "|" in line:
                saved_word, _ = line.split("|", 1)
                if saved_word.strip().lower() == word:
                    output_lines.append(replacement)
                    updated = True
                    continue
            output_lines.append(line)
        if not updated:
            output_lines.append(replacement)
        with open(coach.MEANINGS_FILE, "w") as file:
            file.writelines(output_lines)

    def pending_selection_key(self, selection):
        if len(selection) >= 4:
            selected, word, meaning, raw_line = selection
            return raw_line
        selected, word, meaning = selection
        return f"{word}|{meaning}\n"

    def show_approve_pending_words(self, push=True, selected_keys=None):
        if push:
            self.controller.push_screen("approve_pending_words")
        else:
            self.controller.replace_screen("approve_pending_words")
        if selected_keys is None:
            selected_keys = set()
        self.current_view = "approve_pending_words"
        self.clear()
        self.heading(self.main, "Approve Selected Internet Words")
        self.pending_selection_vars = []
        for word, meaning, raw_line in self.load_pending_word_records():
            selected = tk.BooleanVar(value=raw_line in selected_keys)
            self.pending_selection_vars.append((selected, word, meaning, raw_line))
            tk.Checkbutton(self.main, text=f"{word}: {meaning}", variable=selected, font=("Arial", self.font_size.get()), bg=self.colors()["bg"], fg=self.colors()["fg"]).pack(anchor="w", padx=14, pady=4)
        if not self.pending_selection_vars:
            self.body_text(self.main, "No pending words yet.")
        self.make_button(self.main, "Approve Selected Words", self.approve_selected_pending_words, enabled=bool(self.pending_selection_vars))
        self.make_button(self.main, "Return Home", self.show_home)

    def approve_selected_pending_words(self):
        selected = []
        for selection in self.pending_selection_vars:
            if selection[0].get():
                if len(selection) >= 4:
                    selected.append((selection[1], selection[2], selection[3]))
                else:
                    selected.append((selection[1], selection[2], f"{selection[1]}|{selection[2]}\n"))
        if not selected:
            messagebox.showerror("Choose words", "Select at least one pending word to approve.")
            return
        current_words = coach.load_words()
        for word, meaning, raw_line in selected:
            if word not in current_words:
                current_words.append(word)
        coach.save_words(current_words)
        existing_meanings = coach.load_meanings()
        for word, meaning, raw_line in selected:
            if word not in existing_meanings:
                self.append_or_update_meaning_line(word, meaning)
        selected_line_counts = {}
        for word, meaning, raw_line in selected:
            selected_line_counts[raw_line] = selected_line_counts.get(raw_line, 0) + 1
        try:
            with open(coach.PENDING_WORDS_FILE, "r") as file:
                pending_lines = file.readlines()
        except FileNotFoundError:
            pending_lines = []
        remaining_lines = []
        for line in pending_lines:
            if selected_line_counts.get(line, 0) > 0:
                selected_line_counts[line] -= 1
            else:
                remaining_lines.append(line)
        with open(coach.PENDING_WORDS_FILE, "w") as file:
            file.writelines(remaining_lines)
        self.show_lines("Approve Selected Internet Words", [f"Approved {len(selected)} word(s)."], push=False)


    def back_to_random_choices(self):
        self.controller.back_to_random_choices_from_amount()
        self.show_random_menu(push=False)

    def start_random_from_amount(self):
        valid, amount, message = validate_random_practice_amount(self.amount_var.get(), len(self.random_group_words))
        if not valid:
            messagebox.showerror("Choose a number", message)
            return
        selected_words = select_random_words(self.random_group_words, amount)
        self.auto_scroll.reset_for_new_activity()
        self.controller.start_activity_history()
        self.active_session = RandomPracticeSession(selected_words, coach.load_meanings(), coach.save_missed_word, coach.save_score, coach.pronounce_word)
        self.controller.push_screen("activity_prompt")
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=False, add_to_history=True)

    def start_spelling_test(self, words=None, push=True):
        if push:
            self.controller.push_screen("activity_prompt")
        self.auto_scroll.reset_for_new_activity()
        self.controller.start_activity_history()
        spelling_words = list(words) if words is not None else prepare_spelling_test_words(coach.load_words())
        self.active_session = SpellingTestSession(spelling_words, coach.save_missed_word, coach.save_score, coach.pronounce_word)
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=False, add_to_history=True)

    def show_activity_prompt(self, prompt, push=True, add_to_history=False):
        if push:
            self.controller.push_screen("activity_prompt")
        else:
            self.controller.replace_screen("activity_prompt")
        self.current_view = "activity_prompt"
        self.current_prompt = prompt
        if add_to_history:
            self.controller.add_prompt_to_history(self.active_session.activity_label, prompt)
        self.clear()
        self.auto_scroll.add_active_output()
        self.heading(self.main, self.active_session.activity_label)
        self.update_jump_control_visibility()
        self.render_activity_history()
        self.make_button(self.main, "Repeat Word", self.active_session.repeat_word)
        entry = tk.Entry(self.main, textvariable=self.answer_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda event: self.submit_answer())
        self.make_button(self.main, "Submit", self.submit_answer)
        self.make_button(self.main, "Return Home", self.show_home)
        self.scroll_to_active_if_requested()

    def jump_to_current_question(self):
        self.scroll_events.jump_to_current_question()
        self.update_jump_control_visibility()
        self.canvas.yview_moveto(1.0)
        if self.current_view == "feedback" and self.controller.current_feedback:
            self.show_feedback(self.controller.current_feedback, push=False, add_to_history=False)
        elif self.current_prompt:
            self.show_activity_prompt(self.current_prompt, push=False, add_to_history=False)

    def submit_answer(self):
        if not self.active_session or not self.current_prompt:
            return
        submitted_answer = self.answer_var.get()
        feedback = self.active_session.submit_answer(submitted_answer, expected_word=self.current_prompt.expected_word)
        self.answer_var.set("")
        self.show_feedback(feedback, submitted_answer=submitted_answer, add_to_history=True)

    def show_feedback(self, feedback, push=True, submitted_answer="", add_to_history=False):
        if push:
            self.controller.push_screen("feedback")
        else:
            self.controller.replace_screen("feedback")
        self.current_view = "feedback"
        if add_to_history:
            self.controller.add_feedback_to_history(self.active_session.activity_label, feedback, submitted_answer)
        else:
            self.controller.current_feedback = feedback
        self.clear()
        self.auto_scroll.add_active_output()
        self.heading(self.main, "Feedback")
        self.update_jump_control_visibility()
        self.render_activity_history()
        if not feedback.correct:
            self.make_button(self.main, "Repeat Word", self.active_session.repeat_word)
        if feedback.finished:
            self.make_button(self.main, "Return Home", self.show_home)
        else:
            self.make_button(self.main, "Next Question", self.next_question)
        self.scroll_to_active_if_requested()

    def render_activity_history(self):
        for item in self.controller.activity_history:
            if item.item_type == "prompt":
                text = f"Question {item.question_number} of {item.total_questions}\n{item.instruction}"
                if item.visible_word:
                    text += f"\nWord: {item.visible_word}\nMeaning: {item.meaning}"
            else:
                text = f"Question {item.question_number} of {item.total_questions} feedback\nYour answer: {item.submitted_answer}\n{item.feedback_message}"
                if item.revealed_word:
                    text += f"\nCorrect spelling: {item.revealed_word}"
                if item.score is not None and item.total_answered is not None:
                    text += f"\nActivity complete. Score: {item.score} out of {item.total_answered}"
            self.body_text(self.main, text)

    def next_question(self):
        self.active_session.advance_after_feedback()
        self.current_prompt = self.active_session.start()
        self.show_activity_prompt(self.current_prompt, push=True, add_to_history=True)


def main():
    root = tk.Tk()
    root.geometry("900x700")
    DashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
