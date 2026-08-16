import random
import tkinter as tk
from tkinter import ttk

from common import BaseGame, RoundResult


class NBackGame(BaseGame):
    """
    N-back 전담 모듈.

    상태 흐름:
      자극 표시 -> 응답 대기 -> 응답 확정 -> 다음 자극

    각 자극마다 하나의 타임아웃만 사용하도록 구성해
    중복 next_item() 호출이나 이중 판정을 피한다.
    """

    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)

        self.n = min(4, 1 + (difficulty - 1) // 3)
        self.rounds = 10 + difficulty * 2
        self.interval = max(900, 1900 - difficulty * 90)

        self.sequence = self._make_sequence()

        self.index = -1
        self.correct = 0
        self.total_answerable = max(1, self.rounds - self.n)

        self.awaiting = False
        self.current_is_match = False
        self.timeout_id = None
        self.finished = False

        ttk.Label(
            self,
            text=(
                f"{self.n}-back: 현재 숫자가 "
                f"{self.n}칸 전 숫자와 같은지 판단하세요."
            ),
            font=("맑은 고딕", 13),
        ).pack(pady=(10, 12))

        self.progress = ttk.Progressbar(
            self,
            maximum=self.rounds,
            length=500,
        )
        self.progress.pack(pady=8)

        card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=35,
        )
        card.pack(
            expand=True,
            fill="both",
            padx=70,
            pady=15,
        )

        self.stim = ttk.Label(
            card,
            text="준비",
            style="Big.TLabel",
            anchor="center",
        )
        self.stim.pack(expand=True)

        self.feedback = ttk.Label(
            card,
            text="",
            style="Card.TLabel",
        )
        self.feedback.pack(pady=5)

        buttons = ttk.Frame(self)
        buttons.pack(pady=14)

        self.same_btn = ttk.Button(
            buttons,
            text="같다  [←]",
            style="Game.TButton",
            command=lambda: self.answer(True),
            state="disabled",
        )
        self.same_btn.pack(side="left", padx=8)

        self.diff_btn = ttk.Button(
            buttons,
            text="다르다  [→]",
            style="Game.TButton",
            command=lambda: self.answer(False),
            state="disabled",
        )
        self.diff_btn.pack(side="left", padx=8)

        self.bind_all("<Left>", self._on_left)
        self.bind_all("<Right>", self._on_right)

        self.safe_after(900, self.next_item)

    def _make_sequence(self):
        seq = []

        for i in range(self.rounds):
            if i >= self.n and random.random() < 0.38:
                seq.append(seq[i - self.n])
                continue

            options = list(range(1, 10))

            if i >= self.n:
                target = seq[i - self.n]
                if target in options:
                    options.remove(target)

            seq.append(random.choice(options))

        return seq

    def _on_left(self, _event):
        self.answer(True)

    def _on_right(self, _event):
        self.answer(False)

    def next_item(self):
        if self.finished:
            return

        self.timeout_id = None
        self.index += 1

        if self.index >= self.rounds:
            self.finish_round()
            return

        self.progress["value"] = self.index + 1

        value = self.sequence[self.index]
        self.stim.config(text=str(value))
        self.feedback.config(text="")

        if self.index < self.n:
            self.awaiting = False
            self._set_buttons(False)
            self.timeout_id = self.safe_after(
                self.interval,
                self.next_item,
            )
            return

        self.current_is_match = (
            value == self.sequence[self.index - self.n]
        )

        self.awaiting = True
        self._set_buttons(True)

        self.timeout_id = self.safe_after(
            self.interval,
            self._timeout_current,
        )

    def _timeout_current(self):
        self.timeout_id = None

        if self.finished:
            return

        if self.awaiting:
            self.awaiting = False
            self._set_buttons(False)
            self.feedback.config(text="시간 초과")

        self.safe_after(120, self.next_item)

    def answer(self, same):
        if self.finished or not self.awaiting:
            return

        self.awaiting = False
        self._set_buttons(False)

        if self.timeout_id is not None:
            self.cancel_after(self.timeout_id)
            self.timeout_id = None

        if same == self.current_is_match:
            self.correct += 1
            self.feedback.config(text="정답")
        else:
            self.feedback.config(text="오답")

        self.safe_after(180, self.next_item)

    def _set_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.same_btn.config(state=state)
        self.diff_btn.config(state=state)

    def finish_round(self):
        if self.finished:
            return

        self.finished = True
        self.clear_afters()

        try:
            self.unbind_all("<Left>")
            self.unbind_all("<Right>")
        except tk.TclError:
            pass

        total = self.total_answerable
        accuracy = self.correct / total

        score = int(
            1000
            * accuracy
            * (1 + 0.18 * (self.n - 1))
            * (1 + self.difficulty * 0.05)
        )

        self.host.finish(
            RoundResult(
                score=score,
                correct=self.correct,
                total=total,
                accuracy=accuracy,
                duration=self.elapsed(),
                detail=f"{self.n}-back",
            )
        )