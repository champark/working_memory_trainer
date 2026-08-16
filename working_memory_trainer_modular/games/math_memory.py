import random
import tkinter as tk
from tkinter import ttk

from common import BaseGame, RoundResult
from config import WORDS


class MathMemoryGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)

        self.rounds = min(10, 4 + difficulty // 2)
        self.math_level = 1 + (difficulty - 1) // 3
        self.word_ms = max(
            1000,
            2300 - difficulty * 100,
        )

        self.index = 0
        self.words = random.sample(WORDS, self.rounds)

        self.correct_math = 0
        self.correct_words = 0
        self.current_answer = None
        self.word_entries = []

        ttk.Label(
            self,
            text=(
                "계산 문제를 풀고, "
                "직후 나타나는 단어도 순서대로 기억하세요."
            ),
            font=("맑은 고딕", 13),
        ).pack(pady=(10, 10))

        self.progress = ttk.Progressbar(
            self,
            maximum=self.rounds,
            length=520,
        )
        self.progress.pack(pady=6)

        self.card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=35,
        )
        self.card.pack(
            expand=True,
            fill="both",
            padx=70,
            pady=15,
        )

        self.main = ttk.Label(
            self.card,
            text="",
            style="Big.TLabel",
            anchor="center",
        )
        self.main.pack(expand=True)

        self.info = ttk.Label(
            self.card,
            text="",
            style="Card.TLabel",
        )
        self.info.pack()

        self.answer_var = tk.StringVar()

        self.entry = ttk.Entry(
            self.card,
            textvariable=self.answer_var,
            width=12,
            font=("맑은 고딕", 16),
            justify="center",
        )
        self.entry.pack(pady=12)

        self.entry.bind(
            "<Return>",
            lambda _event: self.submit_math(),
        )

        self.submit_btn = ttk.Button(
            self.card,
            text="정답 입력",
            command=self.submit_math,
        )
        self.submit_btn.pack()

        self.safe_after(500, self.next_math)

    def make_problem(self):
        if self.math_level == 1:
            a = random.randint(2, 20)
            b = random.randint(2, 12)

            if random.random() < 0.5:
                return f"{a} + {b} = ?", a + b

            if b > a:
                a, b = b, a

            return f"{a} - {b} = ?", a - b

        if self.math_level == 2:
            op = random.choice(["+", "-", "×"])

            if op == "×":
                a = random.randint(2, 12)
                b = random.randint(2, 9)
                return f"{a} × {b} = ?", a * b

            a = random.randint(10, 60)
            b = random.randint(3, 30)

            if op == "+":
                return f"{a} + {b} = ?", a + b

            if b > a:
                a, b = b, a

            return f"{a} - {b} = ?", a - b

        op = random.choice(["+", "-", "×", "mix"])

        if op == "mix":
            a = random.randint(10, 40)
            b = random.randint(2, 9)
            c = random.randint(2, 8)
            return f"{a} + {b} × {c} = ?", a + b * c

        if op == "×":
            a = random.randint(4, 18)
            b = random.randint(3, 12)
            return f"{a} × {b} = ?", a * b

        a = random.randint(20, 100)
        b = random.randint(5, 50)

        if op == "+":
            return f"{a} + {b} = ?", a + b

        if b > a:
            a, b = b, a

        return f"{a} - {b} = ?", a - b

    def next_math(self):
        if self.index >= self.rounds:
            self.show_word_recall()
            return

        question, answer = self.make_problem()
        self.current_answer = answer

        self.progress["value"] = self.index
        self.main.config(text=question)
        self.info.config(
            text=f"문제 {self.index + 1} / {self.rounds}"
        )

        self.answer_var.set("")
        self.entry.config(state="normal")
        self.submit_btn.config(state="normal")
        self.entry.focus_set()

    def submit_math(self):
        if str(self.entry["state"]) == "disabled":
            return

        try:
            value = int(self.answer_var.get().strip())
        except ValueError:
            self.info.config(text="숫자로 입력하세요.")
            return

        if value == self.current_answer:
            self.correct_math += 1

        self.entry.config(state="disabled")
        self.submit_btn.config(state="disabled")

        self.show_word()

    def show_word(self):
        word = self.words[self.index]

        self.main.config(text=word)
        self.info.config(text="이 단어를 기억하세요")

        self.index += 1
        self.progress["value"] = self.index

        self.safe_after(self.word_ms, self.next_math)

    def show_word_recall(self):
        self.clear_afters()

        for child in self.winfo_children():
            child.destroy()

        ttk.Label(
            self,
            text="지금까지 나타난 단어를 순서대로 입력하세요.",
            font=("맑은 고딕", 14, "bold"),
        ).pack(pady=12)

        form = ttk.Frame(self)
        form.pack(expand=True)

        for i in range(self.rounds):
            row = ttk.Frame(form)
            row.pack(pady=3)

            ttk.Label(
                row,
                text=f"{i + 1}.",
                width=4,
            ).pack(side="left")

            var = tk.StringVar()
            ent = ttk.Entry(
                row,
                textvariable=var,
                width=22,
            )
            ent.pack(side="left")

            self.word_entries.append(var)

            if i == 0:
                ent.focus_set()

        ttk.Button(
            self,
            text="채점",
            style="Game.TButton",
            command=self.grade,
        ).pack(pady=16)

    def grade(self):
        answers = [
            var.get().strip()
            for var in self.word_entries
        ]

        self.correct_words = sum(
            answer == target
            for answer, target in zip(
                answers,
                self.words,
            )
        )

        total = self.rounds * 2
        correct = self.correct_math + self.correct_words
        accuracy = correct / total

        score = int(
            1000
            * accuracy
            * (1 + self.math_level * 0.08)
            * (1 + self.rounds * 0.035)
        )

        detail = (
            f"계산 {self.correct_math}/{self.rounds}, "
            f"단어 {self.correct_words}/{self.rounds}"
        )

        self.host.finish(
            RoundResult(
                score=score,
                correct=correct,
                total=total,
                accuracy=accuracy,
                duration=self.elapsed(),
                detail=detail,
            )
        )
