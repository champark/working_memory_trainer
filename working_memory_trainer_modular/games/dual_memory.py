import random
import tkinter as tk
from tkinter import ttk

from common import BaseGame, RoundResult
from config import POSITIONS


class DualMemoryGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)

        self.items = min(
            8,
            3 + (difficulty - 1) // 2,
        )
        self.digits = min(
            4,
            2 + (difficulty - 1) // 4,
        )
        self.display_ms = max(
            1200,
            2600 - difficulty * 110,
        )

        self.sequence = []
        self.index = 0
        self.entries = []

        for _ in range(self.items):
            low = 10 ** (self.digits - 1)
            high = 10 ** self.digits - 1

            number = random.randint(low, high)
            pos = random.choice(POSITIONS)

            self.sequence.append((number, pos))

        ttk.Label(
            self,
            text="숫자와 표시 위치를 한 쌍으로 기억하세요.",
            font=("맑은 고딕", 13),
        ).pack(pady=(8, 8))

        self.progress = ttk.Progressbar(
            self,
            maximum=self.items,
            length=520,
        )
        self.progress.pack(pady=6)

        self.board = tk.Frame(
            self,
            bg="white",
            highlightthickness=1,
            highlightbackground="#aaa",
            width=460,
            height=360,
        )
        self.board.pack(expand=True, pady=12)
        self.board.pack_propagate(False)

        self.cells = {}

        for row_index in range(3):
            self.board.grid_rowconfigure(
                row_index,
                weight=1,
                uniform="r",
            )
            self.board.grid_columnconfigure(
                row_index,
                weight=1,
                uniform="c",
            )

            for col_index in range(3):
                cell = tk.Label(
                    self.board,
                    text="",
                    bg="white",
                    font=("맑은 고딕", 22, "bold"),
                    relief="solid",
                    borderwidth=1,
                )
                cell.grid(
                    row=row_index,
                    column=col_index,
                    sticky="nsew",
                    padx=2,
                    pady=2,
                )
                self.cells[(row_index, col_index)] = cell

        self.info = ttk.Label(self, text="")
        self.info.pack(pady=5)

        self.safe_after(600, self.show_item)

    def show_item(self):
        if self.index >= self.items:
            self.show_recall()
            return

        for cell in self.cells.values():
            cell.config(text="", bg="white")

        number, (row, col, _label) = self.sequence[self.index]

        self.cells[(row, col)].config(
            text=str(number),
            bg="#fff3b0",
        )

        self.info.config(
            text=f"{self.index + 1} / {self.items}"
        )
        self.progress["value"] = self.index + 1

        self.index += 1
        self.safe_after(self.display_ms, self.show_item)

    def show_recall(self):
        self.clear_afters()

        for child in self.winfo_children():
            child.destroy()

        ttk.Label(
            self,
            text="각 순서의 숫자와 위치를 입력하세요.",
            font=("맑은 고딕", 14, "bold"),
        ).pack(pady=10)

        ttk.Label(
            self,
            text=(
                "위치는 목록에서 선택합니다. "
                "숫자와 위치를 각각 채점합니다."
            ),
        ).pack(pady=(0, 8))

        form = ttk.Frame(self)
        form.pack(expand=True)

        position_names = [
            position[2]
            for position in POSITIONS
        ]

        for i in range(self.items):
            row = ttk.Frame(form)
            row.pack(pady=4)

            ttk.Label(
                row,
                text=f"{i + 1}번",
                width=5,
            ).pack(side="left")

            number_var = tk.StringVar()
            position_var = tk.StringVar()

            ent = ttk.Entry(
                row,
                textvariable=number_var,
                width=12,
            )
            ent.pack(side="left", padx=5)

            combo = ttk.Combobox(
                row,
                textvariable=position_var,
                values=position_names,
                state="readonly",
                width=16,
            )
            combo.pack(side="left", padx=5)

            self.entries.append(
                (number_var, position_var)
            )

            if i == 0:
                ent.focus_set()

        ttk.Button(
            self,
            text="채점",
            style="Game.TButton",
            command=self.grade,
        ).pack(pady=14)

    def grade(self):
        correct_num = 0
        correct_pos = 0

        for (
            number_var,
            position_var,
        ), (
            number,
            position,
        ) in zip(
            self.entries,
            self.sequence,
        ):
            if number_var.get().strip() == str(number):
                correct_num += 1

            if position_var.get().strip() == position[2]:
                correct_pos += 1

        correct = correct_num + correct_pos
        total = self.items * 2
        accuracy = correct / total

        score = int(
            1000
            * accuracy
            * (1 + self.digits * 0.08)
            * (1 + self.items * 0.04)
        )

        detail = (
            f"숫자 {correct_num}/{self.items}, "
            f"위치 {correct_pos}/{self.items}"
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
