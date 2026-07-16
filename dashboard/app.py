"""Tkinter Dashboard Prototype 1.

Run with: python3 -m dashboard.app
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import reading_spelling_coach as coach
from dashboard.logic import (
    AutoScrollEventController,
    AutoScrollState,
    DashboardController,
    PracticeByLevelSession,
    PracticeMissedWordsSession,
    PracticeWordsSession,
    RandomPracticeSession,
    SpellingTestSession,
    add_word_to_bank,
    approve_pending_indices,
    build_progress_report,
    fetch_internet_suggestions,
    load_dashboard_meanings,
    load_pending_word_records,
    parse_score_line,
    prepare_spelling_test_words,
    read_non_empty_lines,
    save_score_with_activity,
    save_selected_suggestions,
    select_random_words,
    validate_random_practice_amount,
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
        self.answer_var = tk.StringVar()
        self.amount_var = tk.StringVar(value="1")
        self.spelling_count_var = tk.StringVar(value="all")
        self.new_word_var = tk.StringVar()
        self.pronounce_var = tk.StringVar()
        self.internet_topic_var = tk.StringVar(value="computer")
        self.internet_suggestions: list[tuple[str, str]] = []
        self.internet_choice_vars: list[tk.BooleanVar] = []
        self.pending_choice_vars: list[tk.BooleanVar] = []
        self.last_lines_title = ""
        self.last_lines = []
        self.build_shell()
        self.show_home()

    def colors(self):
        if self.high_contrast.get():
            return {"bg": "#000000", "fg": "#ffffff", "card": "#1e1e1e", "button": "#ffd84d", "disabled": "#555555"}
        return {"bg": "#f7f4ea", "fg": "#1f2933", "card": "#ffffff", "button": "#dbeafe", "disabled": "#e5e7eb"}

    def build_shell(self):
        self.root.bind("<Alt-h>", lambda event: self.show_home())
        self.root.bind("<Alt-Left>", lambda event: self.go_back())
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

    def on_linux_scroll_up(self, event):
        self.scroll_events.linux_button_4(self.current_view in ["activity_prompt", "feedback"])
        self.update_jump_control_visibility()
        self.canvas.yview_scroll(-3, "units")

    def on_linux_scroll_down(self, event):
        self.canvas.yview_scroll(3, "units")
        self.root.after_idle(self.maybe_resume_at_bottom)

    def on_keyboard_scroll(self, event):
        self.scroll_events.keyboard_scroll(event.keysym, self.current_view in ["activity_prompt", "feedback"])
        self.update_jump_control_visibility()
        if event.keysym == "Prior":
            self.canvas.yview_scroll(-1, "pages")
        elif event.keysym == "Next":
            self.canvas.yview_scroll(1, "pages")
        elif event.keysym == "Home":
            self.canvas.yview_moveto(0)
        elif event.keysym == "End":
            self.canvas.yview_moveto(1)
            self.root.after_idle(self.maybe_resume_at_bottom)

    def maybe_resume_at_bottom(self):
        if self.canvas.yview()[1] >= 0.99:
            self.auto_scroll.manual_scroll_to_bottom()
            self.update_jump_control_visibility()

    def update_jump_control_visibility(self):
        if self.auto_scroll.should_show_jump_control and self.current_view in ["activity_prompt", "feedback"]:
            if not self.jump_button.winfo_ismapped():
                self.jump_button.pack(side="left", padx=5)
        elif self.jump_button.winfo_ismapped():
            self.jump_button.pack_forget()

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
        self.spacing.set(min(40, self.spacing.get() + 4))
        self.update_accessibility()

    def decrease_spacing(self):
        self.spacing.set(max(2, self.spacing.get() - 4))
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
        button = tk.Button(parent, text=text, command=command if enabled else None, font=("Arial", self.font_size.get()), bg=c["button"] if enabled else c["disabled"], fg="#000000", padx=18, pady=12, takefocus=enabled, state="normal" if enabled else "disabled")
        button.pack(fill="x", pady=max(1, self.spacing.get() // 2))
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
        self.body_text(self.main, "Choose an activity. All 17 dashboard functions are wired to workflows.")
        for group, controls in self.controller.home_model().items():
            frame = tk.LabelFrame(self.main, text=group, font=("Arial", self.font_size.get(), "bold"), padx=14, pady=14, bg=self.colors()["card"], fg=self.colors()["fg"])
            frame.pack(fill="x", padx=14, pady=10)
            for label, activity in controls.items():
                command = self.show_home if activity == "home" else (self.root.destroy if activity == "exit" else lambda activity=activity: self.open_activity(activity))
                self.make_button(frame, label, command, enabled=self.controller.is_functional(activity))
        self.canvas.yview_moveto(0)

    def render_current_view(self):
        saved = (self.answer_var.get(), self.amount_var.get(), self.spelling_count_var.get(), self.new_word_var.get(), self.pronounce_var.get(), self.internet_topic_var.get())
        if self.current_view == "home":
            self.show_home()
        elif self.current_view == "random_menu":
            self.show_random_menu(push=False)
        elif self.current_view == "random_amount":
            self.show_random_amount(push=False)
        elif self.current_view == "spelling_count":
            self.show_spelling_count(push=False)
        elif self.current_view == "level_menu":
            self.show_level_menu(push=False)
        elif self.current_view == "add_word":
            self.show_add_word(push=False)
        elif self.current_view == "pronounce_word":
            self.show_pronounce(push=False)
        elif self.current_view == "internet_words":
            self.show_internet_words(push=False)
        elif self.current_view == "pending_words":
            self.show_pending_words(push=False)
        elif self.current_view == "approve_pending_words":
            self.show_approve_pending_words(push=False)
        elif self.current_view == "activity_prompt" and self.current_prompt:
            self.show_activity_prompt(self.current_prompt, push=False, add_to_history=False)
        elif self.current_view == "feedback" and self.controller.current_feedback:
            self.show_feedback(self.controller.current_feedback, push=False, add_to_history=False)
        elif self.current_view == "lines":
            self.show_lines(self.last_lines_title, self.last_lines, push=False)
        else:
            self.show_home()
        self.answer_var.set(saved[0]); self.amount_var.set(saved[1]); self.spelling_count_var.set(saved[2]); self.new_word_var.set(saved[3]); self.pronounce_var.set(saved[4]); self.internet_topic_var.set(saved[5])

    def go_back(self):
        previous = self.controller.back()
        if previous == "random_menu": self.show_random_menu(push=False)
        elif previous == "random_amount": self.show_random_amount(push=False)
        elif previous == "spelling_count": self.show_spelling_count(push=False)
        elif previous == "level_menu": self.show_level_menu(push=False)
        else: self.show_home()

    def open_activity(self, activity, push=True):
        if activity == "practice_all_words": self.start_practice_all_words(push=push)
        elif activity == "spelling_test": self.show_spelling_count(push=push)
        elif activity == "random_practice": self.show_random_menu(push=push)
        elif activity == "practice_by_level": self.show_level_menu(push=push)
        elif activity == "practice_missed_words": self.start_practice_missed_words(push=push)
        elif activity == "score_history": self.show_score_history(push=push)
        elif activity == "clear_missed_words": self.confirm_clear_missed_words()
        elif activity == "missed_words": self.show_lines("Missed Words", coach.load_missed_words() or ["No missed words saved."], push=push)
        elif activity == "word_list": self.show_lines("Word List", coach.load_words(), push=push)
        elif activity == "word_meanings": self.show_word_meanings(push=push)
        elif activity == "add_word": self.show_add_word(push=push)
        elif activity == "pronounce_word": self.show_pronounce(push=push)
        elif activity == "internet_words": self.show_internet_words(push=push)
        elif activity == "pending_words": self.show_pending_words(push=push)
        elif activity == "approve_pending_words": self.show_approve_pending_words(push=push)
        elif activity == "progress_report": self.show_lines("Progress Report", build_progress_report(), push=push)
        elif activity == "exit": self.root.destroy()

    def show_lines(self, title, lines, push=True):
        if push: self.controller.push_screen("lines")
        self.current_view = "lines"; self.last_lines_title = title; self.last_lines = list(lines)
        self.clear(); self.heading(self.main, title)
        for line in lines: self.body_text(self.main, str(line))
        self.make_button(self.main, "Return Home", self.show_home)
        self.canvas.yview_moveto(0)

    def show_word_meanings(self, push=True):
        meanings = load_dashboard_meanings(coach.load_words())
        self.show_lines("Word Meanings", [f"{w}: {meanings.get(w, 'No meaning saved yet.')}" for w in coach.load_words()], push=push)

    def show_score_history(self, push=True):
        lines = [" | ".join(parse_score_line(line)) for line in read_non_empty_lines(coach.SCORE_HISTORY_FILE)] or ["No scores saved yet."]
        self.show_lines("Score History", lines, push=push)

    def confirm_clear_missed_words(self):
        if messagebox.askyesno("Clear missed words?", "Clear all missed words? This cannot be undone."):
            coach.clear_missed_words(); self.show_lines("Missed Words", ["Missed words cleared."])
        else:
            self.show_lines("Missed Words", ["Missed words were not cleared."])

    def start_practice_all_words(self, push=True):
        self.start_session(PracticeWordsSession(coach.load_words(), load_dashboard_meanings(coach.load_words()), coach.save_missed_word, save_score_with_activity, coach.pronounce_word), push=push)

    def start_practice_missed_words(self, push=True):
        self.start_session(PracticeMissedWordsSession(coach.load_missed_words(), load_dashboard_meanings(), coach.save_missed_word, save_score_with_activity, coach.pronounce_word), push=push)

    def show_level_menu(self, push=True):
        if push: self.controller.push_screen("level_menu")
        self.current_view = "level_menu"; self.clear(); self.heading(self.main, "Practice by Level")
        for level, words in coach.LEVELS.items():
            self.make_button(self.main, level.title(), lambda level=level, words=words: self.start_level_practice(level, words))
        self.make_button(self.main, "Return Home", self.show_home)

    def start_level_practice(self, level, words):
        self.start_session(PracticeByLevelSession(level, words, load_dashboard_meanings(words), coach.save_missed_word, save_score_with_activity, coach.pronounce_word), push=True)

    def show_random_menu(self, push=True):
        if push: self.controller.push_screen("random_menu")
        self.current_view = "random_menu"; self.clear(); self.heading(self.main, "Random Practice")
        options = [("All words", coach.load_words()), ("Easy", coach.LEVELS["easy"]), ("Medium", coach.LEVELS["medium"]), ("Hard", coach.LEVELS["hard"]), ("Cybersecurity", coach.LEVELS["cybersecurity"])]
        for label, words in options: self.make_button(self.main, label, lambda words=words: self.choose_random_group(words))
        self.make_button(self.main, "Return Home", self.show_home)

    def choose_random_group(self, words):
        self.random_group_words = list(words); self.amount_var.set("1"); self.show_random_amount(push=True)

    def show_random_amount(self, push=True):
        if push: self.controller.push_screen("random_amount")
        self.current_view = "random_amount"; self.clear(); self.heading(self.main, "How many random words?")
        self.body_text(self.main, f"Choose 1 through {min(5, len(self.random_group_words))}.")
        entry = tk.Entry(self.main, textvariable=self.amount_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8); entry.focus_set(); entry.bind("<Return>", lambda event: self.start_random_from_amount())
        self.make_button(self.main, "Start Random Practice", self.start_random_from_amount, enabled=bool(self.random_group_words))
        self.make_button(self.main, "Back to Random Practice choices", lambda: self.show_random_menu(push=False))

    def start_random_from_amount(self):
        valid, amount, message = validate_random_practice_amount(self.amount_var.get(), len(self.random_group_words))
        if not valid: messagebox.showerror("Choose a number", message); return
        selected_words = select_random_words(self.random_group_words, amount)
        self.start_session(RandomPracticeSession(selected_words, load_dashboard_meanings(selected_words), coach.save_missed_word, save_score_with_activity, coach.pronounce_word), push=True)

    def show_spelling_count(self, push=True):
        if push: self.controller.push_screen("spelling_count")
        self.current_view = "spelling_count"; self.clear(); self.heading(self.main, "Spelling Test")
        self.body_text(self.main, f"Choose 1 through {len(coach.load_words())}, or type all for All Words.")
        entry = tk.Entry(self.main, textvariable=self.spelling_count_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8); entry.focus_set(); entry.bind("<Return>", lambda event: self.start_spelling_test())
        self.make_button(self.main, "All Words", lambda: (self.spelling_count_var.set("all"), self.start_spelling_test()))
        self.make_button(self.main, "Start Spelling Test", self.start_spelling_test)

    def start_spelling_test(self):
        valid, spelling_words, message = prepare_spelling_test_words(coach.load_words(), self.spelling_count_var.get())
        if not valid: messagebox.showerror("Choose word count", message); return
        self.start_session(SpellingTestSession(spelling_words, coach.save_missed_word, save_score_with_activity, coach.pronounce_word), push=True)

    def start_session(self, session, push=True):
        self.auto_scroll.reset_for_new_activity(); self.controller.start_activity_history(); self.active_session = session
        if push: self.controller.push_screen("activity_prompt")
        self.current_prompt = self.active_session.start(); self.show_activity_prompt(self.current_prompt, push=False, add_to_history=True)

    def show_activity_prompt(self, prompt, push=True, add_to_history=False):
        if push: self.controller.push_screen("activity_prompt")
        self.current_view = "activity_prompt"; self.current_prompt = prompt; self.controller.current_feedback = None
        if add_to_history: self.controller.add_prompt_to_history(self.active_session.activity_label, prompt)
        self.clear(); self.auto_scroll.add_active_output(); self.heading(self.main, self.active_session.activity_label); self.update_jump_control_visibility(); self.render_activity_history()
        self.make_button(self.main, "Repeat Word", self.active_session.repeat_word)
        entry = tk.Entry(self.main, textvariable=self.answer_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8); entry.focus_set(); entry.bind("<Return>", lambda event: self.submit_answer())
        self.make_button(self.main, "Submit", self.submit_answer); self.make_button(self.main, "Return Home", self.show_home); self.scroll_to_active_if_requested()

    def jump_to_current_question(self):
        self.scroll_events.jump_to_current_question(); self.update_jump_control_visibility(); self.canvas.yview_moveto(1.0)

    def submit_answer(self):
        submitted_answer = self.answer_var.get(); feedback = self.active_session.submit_answer(submitted_answer); self.answer_var.set(""); self.show_feedback(feedback, submitted_answer=submitted_answer, add_to_history=True)

    def show_feedback(self, feedback, push=True, submitted_answer="", add_to_history=False):
        if push: self.controller.push_screen("feedback")
        self.current_view = "feedback"
        if add_to_history: self.controller.add_feedback_to_history(self.active_session.activity_label, feedback, submitted_answer)
        else: self.controller.current_feedback = feedback
        self.clear(); self.auto_scroll.add_active_output(); self.heading(self.main, "Feedback"); self.update_jump_control_visibility(); self.render_activity_history()
        if not feedback.correct and feedback.revealed_word: self.make_button(self.main, "Repeat Word", self.active_session.repeat_word)
        self.make_button(self.main, "Return Home" if feedback.finished else "Next Question", self.show_home if feedback.finished else self.next_question)
        self.scroll_to_active_if_requested()

    def render_activity_history(self):
        for item in self.controller.activity_history:
            if item.item_type == "prompt":
                text = f"Question {item.question_number} of {item.total_questions}\n{item.instruction}"
                if item.visible_word: text += f"\nWord: {item.visible_word}\nMeaning: {item.meaning}"
            else:
                text = f"Question {item.question_number} of {item.total_questions} feedback\nYour answer: {item.submitted_answer}\n{item.feedback_message}"
                if item.revealed_word: text += f"\nCorrect spelling: {item.revealed_word}"
                if item.score is not None: text += f"\nActivity complete.\nScore: {item.score} out of {item.total_answered}"
            self.body_text(self.main, text)

    def next_question(self):
        self.current_prompt = self.active_session.start(); self.show_activity_prompt(self.current_prompt, push=False, add_to_history=True)

    def show_add_word(self, push=True):
        if push: self.controller.push_screen("add_word")
        self.current_view = "add_word"; self.clear(); self.heading(self.main, "Add New Word")
        entry = tk.Entry(self.main, textvariable=self.new_word_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8); entry.focus_set(); entry.bind("<Return>", lambda event: self.save_new_word())
        self.make_button(self.main, "Save Word", self.save_new_word)

    def save_new_word(self):
        ok, message, words = add_word_to_bank(self.new_word_var.get()); self.new_word_var.set(""); self.show_lines("Add New Word", [message])

    def show_pronounce(self, push=True):
        if push: self.controller.push_screen("pronounce_word")
        self.current_view = "pronounce_word"; self.clear(); self.heading(self.main, "Pronounce a Word")
        entry = tk.Entry(self.main, textvariable=self.pronounce_var, font=("Arial", self.font_size.get()))
        entry.pack(fill="x", padx=14, pady=14, ipady=8); entry.focus_set(); entry.bind("<Return>", lambda event: self.pronounce_entered_word())
        self.make_button(self.main, "Pronounce", self.pronounce_entered_word)

    def pronounce_entered_word(self):
        word = self.pronounce_var.get().strip()
        if not word: self.show_lines("Pronounce a Word", ["No word to pronounce."]); return
        coach.pronounce_word(word); self.show_lines("Pronounce a Word", [f"Speaking: {word}"])

    def show_internet_words(self, push=True):
        if push: self.controller.push_screen("internet_words")
        self.current_view = "internet_words"; self.clear(); self.heading(self.main, "Internet Words")
        self.body_text(self.main, "Enter a topic. Review suggestions before saving any pending words.")
        tk.Entry(self.main, textvariable=self.internet_topic_var, font=("Arial", self.font_size.get())).pack(fill="x", padx=14, pady=14, ipady=8)
        self.make_button(self.main, "Find Suggestions", self.find_internet_suggestions)
        if self.internet_suggestions:
            self.internet_choice_vars = []
            for word, meaning in self.internet_suggestions:
                var = tk.BooleanVar(value=False); self.internet_choice_vars.append(var)
                tk.Checkbutton(self.main, text=f"{word}: {meaning}", variable=var, font=("Arial", self.font_size.get()), bg=self.colors()["bg"], fg=self.colors()["fg"], wraplength=850, justify="left").pack(anchor="w", padx=14, pady=6)
            self.make_button(self.main, "Save Selected as Pending", self.save_selected_internet_words)

    def find_internet_suggestions(self):
        self.internet_suggestions = fetch_internet_suggestions(self.internet_topic_var.get())
        if not self.internet_suggestions: self.show_lines("Internet Words", ["Internet error or no safe suggestions found. No words were saved."])
        else: self.show_internet_words(push=False)

    def save_selected_internet_words(self):
        selected = {i for i, var in enumerate(self.internet_choice_vars) if var.get()}
        saved = save_selected_suggestions(self.internet_suggestions, selected)
        self.show_lines("Internet Words", [f"Saved {saved} selected word(s) to pending words."])

    def show_pending_words(self, push=True):
        records = load_pending_word_records()
        lines = [f"{word}: {meaning}" for word, meaning in records] or ["No pending words yet."]
        self.show_lines("Pending Internet Words", lines, push=push)
        self.current_view = "pending_words"

    def show_approve_pending_words(self, push=True):
        if push: self.controller.push_screen("approve_pending_words")
        self.current_view = "approve_pending_words"; self.clear(); self.heading(self.main, "Approve Internet Words")
        records = load_pending_word_records(); self.pending_choice_vars = []
        if not records: self.body_text(self.main, "No pending words yet.")
        for word, meaning in records:
            var = tk.BooleanVar(value=False); self.pending_choice_vars.append(var)
            tk.Checkbutton(self.main, text=f"{word}: {meaning}", variable=var, font=("Arial", self.font_size.get()), bg=self.colors()["bg"], fg=self.colors()["fg"], wraplength=850, justify="left").pack(anchor="w", padx=14, pady=6)
        self.make_button(self.main, "Approve Selected", self.approve_selected_pending_words, enabled=bool(records))

    def approve_selected_pending_words(self):
        selected = {i for i, var in enumerate(self.pending_choice_vars) if var.get()}
        count, remaining = approve_pending_indices(selected)
        self.show_lines("Approve Internet Words", [f"Approved {count} selected word(s).", f"Remaining pending words: {len(remaining)}"])


def main():
    root = tk.Tk()
    root.geometry("900x700")
    DashboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
