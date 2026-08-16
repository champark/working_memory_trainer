import random
import tkinter as tk
from tkinter import ttk

from common import BaseGame, RoundResult
from config import WORDS


class UpdatingGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)

        self.slots = min(7, 3 + (difficulty - 1) // 2)
        self.updates_count = 3 + difficulty
        self.display_ms = max(
            1800,
            3800 - difficulty * 140,
        )

        self.memory = random.sample(WORDS, self.slots)
        self.updates = []
        self.step = -1
        self.entry_vars = []

        ttk.Label(
            self,
            text=(
                "처음 목록을 기억한 뒤, "
                "지시에 따라 머릿속 목록을 계속 갱신하세요."
            ),
            font=("맑은 고딕", 13),
        ).pack(pady=(10, 8))

        self.progress = ttk.Progressbar(
            self,
            maximum=self.updates_count + 1,
            length=520,
        )
        self.progress.pack(pady=8)

        self.card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=30,
        )
        self.card.pack(
            expand=True,
            fill="both",
            padx=60,
            pady=15,
        )

        self.main = ttk.Label(
            self.card,
            text="",
            font=("맑은 고딕", 25, "bold"),
            background="white",
            anchor="center",
            justify="center",
            wraplength=650,
        )
        self.main.pack(expand=True)

        self.sub = ttk.Label(
            self.card,
            text="",
            style="Card.TLabel",
            anchor="center",
        )
        self.sub.pack(pady=8)

        self.safe_after(500, self.show_initial)

    def show_initial(self):
        text = "   ·   ".join(
            f"{i + 1}. {word}"
            for i, word in enumerate(self.memory)
        )

        self.main.config(text=text)
        self.sub.config(
            text=f"{self.slots}개 단어를 기억하세요"
        )
        self.progress["value"] = 1

        self.safe_after(
            self.display_ms + 800,
            self.prepare_updates,
        )

    def prepare_updates(self):
        used_recent = set(self.memory)

        for _ in range(self.updates_count):
            idx = random.randrange(self.slots)

            choices = [
                word
                for word in WORDS
                if word not in used_recent
            ]
            if not choices:
                choices = WORDS

            new_word = random.choice(choices)
            self.updates.append((idx, new_word))
            used_recent.add(new_word)

        self.step = 0
        self.show_update()

    def show_update(self):
        if self.step >= len(self.updates):
            self.show_recall()
            return

        idx, word = self.updates[self.step]
        self.memory[idx] = word

        self.main.config(
            text=f"{idx + 1}번째 단어를\n\n‘{word}’(으)로 변경"
        )
        self.sub.config(
            text=f"갱신 {self.step + 1} / {self.updates_count}"
        )
        self.progress["value"] = self.step + 2

        self.step += 1
        self.safe_after(self.display_ms, self.show_update)

    def show_recall(self):
        self.clear_afters()
        self.card.destroy()

        ttk.Label(
            self,
            text="현재 기억하고 있는 단어를 순서대로 입력하세요.",
            font=("맑은 고딕", 14, "bold"),
        ).pack(pady=14)

        form = ttk.Frame(self)
        form.pack(expand=True, pady=10)

        for i in range(self.slots):
            row = ttk.Frame(form)
            row.pack(pady=5)

            ttk.Label(
                row,
                text=f"{i + 1}번",
                width=6,
            ).pack(side="left")

            var = tk.StringVar()
            ent = ttk.Entry(
                row,
                textvariable=var,
                width=24,
                font=("맑은 고딕", 12),
            )
            ent.pack(side="left")

            self.entry_vars.append(var)

            if i == 0:
                ent.focus_set()

        ttk.Button(
            form,
            text="채점",
            style="Game.TButton",
            command=self.grade,
        ).pack(pady=14)

    def grade(self):
        answers = [
            var.get().strip()
            for var in self.entry_vars
        ]

        correct = sum(
            answer == target
            for answer, target in zip(
                answers,
                self.memory,
            )
        )

        total = self.slots
        accuracy = correct / total

        score = int(
            1000
            * accuracy
            * (1 + self.slots * 0.06)
            * (1 + self.updates_count * 0.035)
        )

        self.host.finish(
            RoundResult(
                score=score,
                correct=correct,
                total=total,
                accuracy=accuracy,
                duration=self.elapsed(),
                detail=(
                    f"{self.slots}칸 · "
                    f"{self.updates_count}회 갱신"
                ),
            )
        )
