import random
import tkinter as tk
from tkinter import ttk, messagebox

from config import (
    APP_TITLE,
    WINDOW_SIZE,
    WINDOW_MIN_SIZE,
    SAVE_FILE,
    MODE_LABELS,
    TRAINING_MODES,
    AUTO_DIFFICULTY_UP,
    AUTO_DIFFICULTY_DOWN,
    MAX_DIFFICULTY,
    MIN_DIFFICULTY,
)
from games import GAME_CLASSES
from stats import StatsStore


class WorkingMemoryApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(*WINDOW_MIN_SIZE)
        self.configure(bg="#f5f6fa")

        self.stats = StatsStore(SAVE_FILE)
        self.current_frame = None

        self._setup_style()
        self.show_menu()

    def _setup_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("맑은 고딕", 26, "bold"),
            background="#f5f6fa",
        )
        style.configure(
            "Sub.TLabel",
            font=("맑은 고딕", 11),
            background="#f5f6fa",
            foreground="#555",
        )
        style.configure(
            "Menu.TButton",
            font=("맑은 고딕", 13, "bold"),
            padding=14,
        )
        style.configure(
            "Game.TButton",
            font=("맑은 고딕", 12, "bold"),
            padding=10,
        )
        style.configure(
            "Card.TFrame",
            background="white",
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Card.TLabel",
            background="white",
            font=("맑은 고딕", 11),
        )
        style.configure(
            "Big.TLabel",
            background="white",
            font=("맑은 고딕", 34, "bold"),
        )
        style.configure(
            "Difficulty.TRadiobutton",
            font=("맑은 고딕", 11),
            padding=5,
        )

    def swap(self, frame_cls, *args, **kwargs):
        if self.current_frame is not None:
            self.current_frame.destroy()

        self.current_frame = frame_cls(
            self,
            *args,
            **kwargs,
        )
        self.current_frame.pack(
            fill="both",
            expand=True,
        )

    def show_menu(self):
        self.swap(MenuFrame)

    def choose_difficulty(self, mode):
        """
        게임 시작 전 난이도 선택 화면으로 이동한다.

        기본 선택은 '자동'이다.
        자동을 그대로 사용하면 저장된 게임별 난이도로 시작한다.
        """
        self.swap(
            DifficultySelectFrame,
            mode,
        )

    def start_mode(
        self,
        mode,
        random_session=False,
        manual_difficulty=None,
    ):
        """
        manual_difficulty:
            None  -> 자동 난이도
            1~10  -> 해당 세션만 수동 난이도

        수동 난이도는 자동 난이도 기록을 변경하지 않는다.
        """
        if mode == "random":
            chosen = random.choice(TRAINING_MODES)

            self.swap(
                GameHost,
                chosen,
                True,
                manual_difficulty,
            )
        else:
            self.swap(
                GameHost,
                mode,
                random_session,
                manual_difficulty,
            )

    def show_stats(self):
        self.swap(StatsFrame)


# =========================================================
# 메인 메뉴
# =========================================================

class MenuFrame(ttk.Frame):
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.configure(padding=30)

        ttk.Label(
            self,
            text="작업기억 트레이닝",
            style="Title.TLabel",
        ).pack(pady=(15, 6))

        ttk.Label(
            self,
            text=(
                "기억을 유지하면서 "
                "비교·갱신·계산·조작하는 훈련 모음"
            ),
            style="Sub.TLabel",
        ).pack(pady=(0, 25))

        grid = ttk.Frame(self)
        grid.pack(expand=True)

        buttons = [
            (
                "🔢  N-back",
                "nback",
                "몇 단계 전의 자극과 현재 자극을 비교",
            ),
            (
                "🔄  기억 갱신",
                "updating",
                "기억 목록의 특정 항목을 계속 교체",
            ),
            (
                "🧮  계산 + 기억",
                "math_memory",
                "계산을 하면서 단어 순서를 함께 유지",
            ),
            (
                "🧠  이중 기억",
                "dual",
                "숫자와 위치를 동시에 기억",
            ),
            (
                "🎯  랜덤 훈련",
                "random",
                "네 가지 훈련 중 하나를 무작위 선택",
            ),
        ]

        for i, (title, mode, desc) in enumerate(buttons):
            card = ttk.Frame(
                grid,
                style="Card.TFrame",
                padding=16,
            )
            card.grid(
                row=i // 2,
                column=i % 2,
                padx=10,
                pady=10,
                sticky="nsew",
            )

            ttk.Button(
                card,
                text=title,
                style="Menu.TButton",
                command=lambda m=mode: app.choose_difficulty(m),
            ).pack(fill="x")

            ttk.Label(
                card,
                text=desc,
                style="Card.TLabel",
                wraplength=300,
            ).pack(pady=(8, 0))

        for col in range(2):
            grid.columnconfigure(col, weight=1)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(22, 5))

        ttk.Button(
            bottom,
            text="📊 기록 보기",
            command=app.show_stats,
        ).pack(side="left")

        ttk.Button(
            bottom,
            text="종료",
            command=app.destroy,
        ).pack(side="right")


# =========================================================
# 난이도 선택 화면
# =========================================================

class DifficultySelectFrame(ttk.Frame):
    """
    기본 선택은 자동 난이도.

    자동:
        해당 게임의 stats에 저장된 현재 난이도를 사용.

    수동 1~10:
        선택한 세션에서만 해당 난이도를 사용.
        자동 난이도 기록은 변경하지 않는다.
    """

    AUTO_VALUE = 0

    def __init__(self, app, mode):
        super().__init__(app)

        self.app = app
        self.mode = mode

        self.configure(padding=30)

        self.difficulty_var = tk.IntVar(
            value=self.AUTO_VALUE
        )

        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Button(
            header,
            text="← 메뉴",
            command=app.show_menu,
        ).pack(side="left")

        ttk.Label(
            header,
            text="난이도 선택",
            font=("맑은 고딕", 22, "bold"),
        ).pack(side="left", padx=16)

        ttk.Separator(
            self,
            orient="horizontal",
        ).pack(fill="x", pady=15)

        if mode == "random":
            game_title = "랜덤 훈련"
            current_text = (
                "자동을 선택하면 무작위로 뽑힌 게임의 "
                "현재 기록 난이도를 사용합니다."
            )
        else:
            game_title = MODE_LABELS[mode]

            saved_difficulty = (
                self.app.stats.get_difficulty(mode)
            )

            current_text = (
                f"현재 기록에 저장된 자동 난이도: "
                f"{saved_difficulty}"
            )

        ttk.Label(
            self,
            text=game_title,
            font=("맑은 고딕", 20, "bold"),
        ).pack(pady=(25, 8))

        ttk.Label(
            self,
            text=current_text,
            font=("맑은 고딕", 11),
        ).pack(pady=(0, 18))

        card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=25,
        )
        card.pack(
            padx=80,
            pady=10,
            fill="x",
        )

        auto_row = ttk.Frame(card)
        auto_row.pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Radiobutton(
            auto_row,
            text="자동",
            variable=self.difficulty_var,
            value=self.AUTO_VALUE,
            style="Difficulty.TRadiobutton",
            command=self._update_description,
        ).pack(side="left")

        if mode == "random":
            auto_desc = (
                "선택된 게임의 저장된 난이도를 사용"
            )
        else:
            auto_desc = (
                f"현재 {self.app.stats.get_difficulty(mode)}단계 사용"
            )

        self.auto_info = ttk.Label(
            auto_row,
            text=auto_desc,
            font=("맑은 고딕", 10),
            foreground="#555555",
        )
        self.auto_info.pack(
            side="left",
            padx=14,
        )

        ttk.Separator(
            card,
            orient="horizontal",
        ).pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Label(
            card,
            text="수동 난이도",
            style="Card.TLabel",
            font=("맑은 고딕", 11, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 8),
        )

        level_grid = ttk.Frame(card)
        level_grid.pack()

        for level in range(
            MIN_DIFFICULTY,
            MAX_DIFFICULTY + 1,
        ):
            radio = ttk.Radiobutton(
                level_grid,
                text=str(level),
                variable=self.difficulty_var,
                value=level,
                style="Difficulty.TRadiobutton",
                command=self._update_description,
            )

            radio.grid(
                row=(level - 1) // 5,
                column=(level - 1) % 5,
                padx=12,
                pady=7,
                sticky="w",
            )

        self.description_label = ttk.Label(
            self,
            text="",
            font=("맑은 고딕", 11),
            justify="center",
        )
        self.description_label.pack(
            pady=(20, 12),
        )

        ttk.Button(
            self,
            text="훈련 시작",
            style="Menu.TButton",
            command=self._start,
        ).pack(
            pady=10,
        )

        self._update_description()

    def _update_description(self):
        selected = self.difficulty_var.get()

        if selected == self.AUTO_VALUE:
            if self.mode == "random":
                text = (
                    "자동 모드: 무작위로 선택된 게임의 "
                    "저장된 난이도로 시작합니다."
                )
            else:
                saved = self.app.stats.get_difficulty(
                    self.mode
                )

                text = (
                    f"자동 모드: 기록에 저장된 "
                    f"{saved}단계로 시작합니다."
                )
        else:
            text = (
                f"수동 모드: 이번 훈련만 "
                f"{selected}단계로 시작합니다.\n"
                f"훈련 결과는 기록되지만 자동 난이도 값은 "
                f"올라가거나 내려가지 않습니다."
            )

        self.description_label.config(
            text=text
        )

    def _start(self):
        selected = self.difficulty_var.get()

        manual_difficulty = (
            None
            if selected == self.AUTO_VALUE
            else selected
        )

        self.app.start_mode(
            self.mode,
            manual_difficulty=manual_difficulty,
        )


# =========================================================
# 게임 공통 호스트
# =========================================================

class GameHost(ttk.Frame):
    def __init__(
        self,
        app,
        mode,
        random_session=False,
        manual_difficulty=None,
    ):
        super().__init__(app)

        self.app = app
        self.mode = mode
        self.random_session = random_session

        self.manual_difficulty = manual_difficulty

        self.is_manual = (
            manual_difficulty is not None
        )

        self.game = None
        self.actual_difficulty = None

        self.configure(padding=20)

        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Button(
            header,
            text="← 메뉴",
            command=app.show_menu,
        ).pack(side="left")

        title = MODE_LABELS[mode]

        if random_session:
            title = f"랜덤 훈련 · {title}"

        ttk.Label(
            header,
            text=title,
            font=("맑은 고딕", 20, "bold"),
        ).pack(side="left", padx=18)

        self.diff_label = ttk.Label(
            header,
            text="",
        )
        self.diff_label.pack(side="right")

        ttk.Separator(
            self,
            orient="horizontal",
        ).pack(fill="x", pady=12)

        self.body = ttk.Frame(self)
        self.body.pack(
            fill="both",
            expand=True,
        )

        self.start_game()

    def start_game(self):
        if self.is_manual:
            difficulty = self.manual_difficulty
        else:
            difficulty = (
                self.app.stats.get_difficulty(
                    self.mode
                )
            )

        self.actual_difficulty = difficulty

        if self.is_manual:
            diff_text = (
                f"수동 난이도 {difficulty}"
            )
        else:
            diff_text = (
                f"자동 난이도 {difficulty}"
            )

        self.diff_label.config(
            text=diff_text
        )

        game_class = GAME_CLASSES[
            self.mode
        ]

        self.game = game_class(
            self,
            self.body,
            difficulty,
        )

        self.game.pack(
            fill="both",
            expand=True,
        )

    def finish(self, result):
        used_difficulty = (
            self.actual_difficulty
        )

        if not self.is_manual:
            old_auto_diff = (
                self.app.stats.get_difficulty(
                    self.mode
                )
            )

            new_auto_diff = old_auto_diff

            if result.total >= 3:
                if (
                    result.accuracy
                    >= AUTO_DIFFICULTY_UP
                ):
                    new_auto_diff = min(
                        MAX_DIFFICULTY,
                        old_auto_diff + 1,
                    )

                elif (
                    result.accuracy
                    < AUTO_DIFFICULTY_DOWN
                ):
                    new_auto_diff = max(
                        MIN_DIFFICULTY,
                        old_auto_diff - 1,
                    )

            self.app.stats.set_difficulty(
                self.mode,
                new_auto_diff,
            )

        else:
            old_auto_diff = (
                self.app.stats.get_difficulty(
                    self.mode
                )
            )

            new_auto_diff = old_auto_diff

        self.app.stats.add_result(
            self.mode,
            result,
            used_difficulty,
        )

        if self.game is not None:
            self.game.destroy()
            self.game = None

        ResultPanel(
            self,
            self.body,
            result,
            self.mode,
            used_difficulty,
            old_auto_diff,
            new_auto_diff,
            self.random_session,
            self.manual_difficulty,
        ).pack(
            fill="both",
            expand=True,
        )


# =========================================================
# 결과 화면
# =========================================================

class ResultPanel(ttk.Frame):
    def __init__(
        self,
        host,
        parent,
        result,
        mode,
        used_difficulty,
        old_auto_diff,
        new_auto_diff,
        random_session,
        manual_difficulty,
    ):
        super().__init__(parent)

        self.host = host
        self.app = host.app
        self.mode = mode
        self.random_session = random_session
        self.manual_difficulty = manual_difficulty

        self.is_manual = (
            manual_difficulty is not None
        )

        ttk.Label(
            self,
            text="훈련 완료",
            font=("맑은 고딕", 24, "bold"),
        ).pack(
            pady=(35, 12)
        )

        card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=30,
        )
        card.pack(
            padx=90,
            pady=10,
            fill="x",
        )

        ttk.Label(
            card,
            text=f"점수  {result.score:,}",
            font=("맑은 고딕", 25, "bold"),
            background="white",
        ).pack(
            pady=5
        )

        ttk.Label(
            card,
            text=(
                f"정확도  "
                f"{result.accuracy * 100:.1f}% "
                f"({result.correct}/{result.total})"
            ),
            style="Card.TLabel",
        ).pack(
            pady=4
        )

        ttk.Label(
            card,
            text=(
                f"사용 난이도  {used_difficulty}"
            ),
            style="Card.TLabel",
        ).pack(
            pady=4
        )

        ttk.Label(
            card,
            text=(
                f"소요 시간  {result.duration:.1f}초"
            ),
            style="Card.TLabel",
        ).pack(
            pady=4
        )

        if result.detail:
            ttk.Label(
                card,
                text=result.detail,
                style="Card.TLabel",
            ).pack(
                pady=4
            )

        if self.is_manual:
            msg = (
                f"수동 난이도 {used_difficulty}로 "
                f"플레이했습니다.\n"
                f"저장된 자동 난이도는 "
                f"{old_auto_diff}로 유지됩니다."
            )

        elif new_auto_diff > old_auto_diff:
            msg = (
                f"정확도가 높아 자동 난이도가 "
                f"{old_auto_diff} → "
                f"{new_auto_diff}로 상승했습니다."
            )

        elif new_auto_diff < old_auto_diff:
            msg = (
                f"정확도가 낮아 자동 난이도가 "
                f"{old_auto_diff} → "
                f"{new_auto_diff}로 조정되었습니다."
            )

        else:
            msg = (
                f"자동 난이도 "
                f"{old_auto_diff} 유지"
            )

        ttk.Label(
            self,
            text=msg,
            font=("맑은 고딕", 12),
            justify="center",
        ).pack(
            pady=12
        )

        if result.accuracy >= 0.9:
            eval_text = (
                "매우 안정적입니다. "
                "다음 난이도에서도 정확도를 유지해 보세요."
            )

        elif result.accuracy >= 0.75:
            eval_text = (
                "좋습니다. "
                "속도보다 정확도를 먼저 유지하는 편이 좋습니다."
            )

        elif result.accuracy >= 0.6:
            eval_text = (
                "적당히 어려운 구간입니다. "
                "같은 유형을 한 번 더 해볼 만합니다."
            )

        else:
            if self.is_manual:
                eval_text = (
                    "현재 수동 난이도의 부하가 높았습니다. "
                    "다음에는 한 단계 낮춰서 연습해도 좋습니다."
                )
            else:
                eval_text = (
                    "부하가 조금 높았습니다. "
                    "자동 난이도가 필요하면 완화됩니다."
                )

        ttk.Label(
            self,
            text=eval_text,
        ).pack(
            pady=(0, 18)
        )

        buttons = ttk.Frame(self)
        buttons.pack(
            pady=8
        )

        ttk.Button(
            buttons,
            text="같은 훈련 다시",
            style="Game.TButton",
            command=self._retry_same,
        ).pack(
            side="left",
            padx=7,
        )

        ttk.Button(
            buttons,
            text="난이도 다시 선택",
            style="Game.TButton",
            command=lambda: (
                self.app.choose_difficulty(
                    self.mode
                )
            ),
        ).pack(
            side="left",
            padx=7,
        )

        ttk.Button(
            buttons,
            text="메뉴",
            style="Game.TButton",
            command=self.app.show_menu,
        ).pack(
            side="left",
            padx=7,
        )

    def _retry_same(self):
        self.app.start_mode(
            self.mode,
            random_session=self.random_session,
            manual_difficulty=self.manual_difficulty,
        )


# =========================================================
# 기록 화면
# =========================================================

class StatsFrame(ttk.Frame):
    def __init__(self, app):
        super().__init__(app)

        self.app = app
        self.configure(padding=24)

        data = app.stats.data

        header = ttk.Frame(self)
        header.pack(fill="x")

        ttk.Button(
            header,
            text="← 메뉴",
            command=app.show_menu,
        ).pack(side="left")

        ttk.Label(
            header,
            text="훈련 기록",
            font=("맑은 고딕", 22, "bold"),
        ).pack(
            side="left",
            padx=16,
        )

        ttk.Button(
            header,
            text="기록 초기화",
            command=self.reset_stats,
        ).pack(
            side="right"
        )

        summary = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=18,
        )
        summary.pack(
            fill="x",
            pady=18,
        )

        if data["total_games"]:
            avg = (
                data["total_score"]
                / data["total_games"]
            )
        else:
            avg = 0

        ttk.Label(
            summary,
            text=(
                f"총 훈련 "
                f"{data['total_games']}회"
            ),
            style="Card.TLabel",
        ).pack(
            side="left",
            padx=15,
        )

        ttk.Label(
            summary,
            text=(
                f"최고 점수 "
                f"{data['best_score']:,}"
            ),
            style="Card.TLabel",
        ).pack(
            side="left",
            padx=15,
        )

        ttk.Label(
            summary,
            text=(
                f"평균 점수 "
                f"{avg:,.0f}"
            ),
            style="Card.TLabel",
        ).pack(
            side="left",
            padx=15,
        )

        diff_frame = ttk.LabelFrame(
            self,
            text="현재 자동 난이도",
            padding=12,
        )
        diff_frame.pack(
            fill="x",
            pady=(0, 14),
        )

        for mode in TRAINING_MODES:
            ttk.Label(
                diff_frame,
                text=(
                    f"{MODE_LABELS[mode]}: "
                    f"{data['difficulty'].get(mode, 1)}"
                ),
            ).pack(
                side="left",
                padx=16,
            )

        columns = (
            "time",
            "mode",
            "score",
            "accuracy",
            "difficulty",
            "detail",
        )

        tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=16,
        )

        tree.heading(
            "time",
            text="시간",
        )
        tree.heading(
            "mode",
            text="훈련",
        )
        tree.heading(
            "score",
            text="점수",
        )
        tree.heading(
            "accuracy",
            text="정확도",
        )
        tree.heading(
            "difficulty",
            text="사용 난이도",
        )
        tree.heading(
            "detail",
            text="상세",
        )

        tree.column(
            "time",
            width=125,
            anchor="center",
        )
        tree.column(
            "mode",
            width=100,
            anchor="center",
        )
        tree.column(
            "score",
            width=75,
            anchor="center",
        )
        tree.column(
            "accuracy",
            width=75,
            anchor="center",
        )
        tree.column(
            "difficulty",
            width=80,
            anchor="center",
        )
        tree.column(
            "detail",
            width=220,
            anchor="w",
        )

        tree.pack(
            fill="both",
            expand=True,
        )

        for item in reversed(
            data["history"][-50:]
        ):
            tree.insert(
                "",
                "end",
                values=(
                    item.get(
                        "time",
                        "",
                    ),
                    MODE_LABELS.get(
                        item.get("mode"),
                        item.get(
                            "mode",
                            "",
                        ),
                    ),
                    f"{item.get('score', 0):,}",
                    (
                        f"{item.get('accuracy', 0) * 100:.1f}%"
                    ),
                    item.get(
                        "difficulty",
                        1,
                    ),
                    item.get(
                        "detail",
                        "",
                    ),
                ),
            )

    def reset_stats(self):
        if messagebox.askyesno(
            "기록 초기화",
            (
                "모든 훈련 기록과 "
                "자동 난이도를 초기화할까요?"
            ),
        ):
            self.app.stats.reset()
            self.app.show_stats()


def main():
    app = WorkingMemoryApp()
    app.mainloop()


if __name__ == "__main__":
    main()