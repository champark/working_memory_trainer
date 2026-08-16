import random
import time
import tkinter as tk
from tkinter import ttk

from common import BaseGame, RoundResult


class NBackGame(BaseGame):
    """
    N-back 전담 모듈.

    이번 버전의 핵심:
    1. 같은 숫자가 연속으로 나와도 새 자극임을 알 수 있도록
       자극 사이에 짧은 공백을 넣는다.
    2. 현재 자극 번호를 표시한다.
    3. 화면 아래에 남은 시간(초)과 감소하는 제한시간 바를 표시한다.
    4. 응답/시간초과/다음 자극 타이머가 겹치지 않도록
       각 단계의 타이머를 명확히 분리한다.
    """

    STIMULUS_GAP_MS = 140
    ANSWER_FEEDBACK_MS = 220
    TIMER_REFRESH_MS = 40

    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)

        # -------------------------------------------------
        # 난이도 설정
        # -------------------------------------------------
        self.n = min(4, 1 + (difficulty - 1) // 3)
        self.rounds = 10 + difficulty * 2

        # 숫자가 화면에 표시된 뒤 다음 판정까지 허용되는 시간
        self.interval = max(
            900,
            1900 - difficulty * 90,
        )

        self.sequence = self._make_sequence()

        # -------------------------------------------------
        # 게임 상태
        # -------------------------------------------------
        self.index = -1
        self.correct = 0
        self.total_answerable = max(
            1,
            self.rounds - self.n,
        )

        self.awaiting = False
        self.current_is_match = False
        self.finished = False

        # 현재 활성 타이머 ID
        self.timeout_id = None
        self.timer_tick_id = None
        self.transition_id = None

        # 제한시간 표시용
        self.timer_started_at = None
        self.timer_duration_sec = (
            self.interval / 1000.0
        )
        self.timer_answerable = False

        # -------------------------------------------------
        # 시간 바 스타일
        # -------------------------------------------------
        style = ttk.Style(self)

        style.configure(
            "NBackTimeGood.Horizontal.TProgressbar",
            troughcolor="#e4e7eb",
            background="#4caf50",
        )
        style.configure(
            "NBackTimeWarn.Horizontal.TProgressbar",
            troughcolor="#e4e7eb",
            background="#f0a000",
        )
        style.configure(
            "NBackTimeDanger.Horizontal.TProgressbar",
            troughcolor="#e4e7eb",
            background="#d94b4b",
        )

        # -------------------------------------------------
        # 상단 설명
        # -------------------------------------------------
        ttk.Label(
            self,
            text=(
                f"{self.n}-back: 현재 숫자가 "
                f"{self.n}칸 전 숫자와 같은지 판단하세요."
            ),
            font=("맑은 고딕", 13),
        ).pack(
            pady=(10, 6)
        )

        ttk.Label(
            self,
            text=(
                "같은 숫자가 연속으로 나와도 "
                "숫자 사이의 짧은 공백이 새 자극을 구분해 줍니다."
            ),
            font=("맑은 고딕", 10),
            foreground="#666666",
        ).pack(
            pady=(0, 8)
        )

        # 전체 진행도
        self.progress = ttk.Progressbar(
            self,
            maximum=self.rounds,
            length=500,
        )
        self.progress.pack(
            pady=(4, 5)
        )

        self.round_label = ttk.Label(
            self,
            text=f"자극 0 / {self.rounds}",
            font=("맑은 고딕", 10),
        )
        self.round_label.pack(
            pady=(0, 5)
        )

        # -------------------------------------------------
        # 숫자 표시 카드
        # -------------------------------------------------
        card = ttk.Frame(
            self,
            style="Card.TFrame",
            padding=35,
        )
        card.pack(
            expand=True,
            fill="both",
            padx=70,
            pady=12,
        )

        self.stim = ttk.Label(
            card,
            text="준비",
            style="Big.TLabel",
            anchor="center",
        )
        self.stim.pack(
            expand=True
        )

        self.feedback = ttk.Label(
            card,
            text="",
            style="Card.TLabel",
            font=("맑은 고딕", 11, "bold"),
        )
        self.feedback.pack(
            pady=5
        )

        # -------------------------------------------------
        # 응답 버튼
        # -------------------------------------------------
        buttons = ttk.Frame(self)
        buttons.pack(
            pady=(8, 5)
        )

        self.same_btn = ttk.Button(
            buttons,
            text="같다  [←]",
            style="Game.TButton",
            command=lambda: self.answer(True),
            state="disabled",
        )
        self.same_btn.pack(
            side="left",
            padx=8,
        )

        self.diff_btn = ttk.Button(
            buttons,
            text="다르다  [→]",
            style="Game.TButton",
            command=lambda: self.answer(False),
            state="disabled",
        )
        self.diff_btn.pack(
            side="left",
            padx=8,
        )

        # -------------------------------------------------
        # 하단 제한시간 표시
        # -------------------------------------------------
        timer_box = ttk.Frame(self)
        timer_box.pack(
            pady=(5, 12)
        )

        self.timer_label = ttk.Label(
            timer_box,
            text="제한시간 준비",
            font=("맑은 고딕", 11, "bold"),
            anchor="center",
        )
        self.timer_label.pack(
            pady=(0, 4)
        )

        self.time_bar = ttk.Progressbar(
            timer_box,
            maximum=1000,
            value=0,
            length=500,
            style="NBackTimeGood.Horizontal.TProgressbar",
        )
        self.time_bar.pack()

        ttk.Label(
            timer_box,
            text=(
                "바가 모두 줄어들기 전에 "
                "← 같다 / → 다르다 를 선택하세요."
            ),
            font=("맑은 고딕", 9),
            foreground="#777777",
        ).pack(
            pady=(4, 0)
        )

        # 키보드 조작
        self.bind_all(
            "<Left>",
            self._on_left,
        )
        self.bind_all(
            "<Right>",
            self._on_right,
        )

        self.safe_after(
            900,
            self.next_item,
        )

    # =====================================================
    # 문제 생성
    # =====================================================

    def _make_sequence(self):
        seq = []

        for i in range(self.rounds):
            # 약 38% 확률로 실제 N-back 일치 자극 생성
            if (
                i >= self.n
                and random.random() < 0.38
            ):
                seq.append(
                    seq[i - self.n]
                )
                continue

            # 일치가 아닌 문제는 우연히 N-back 값과 같아지는 것을 방지
            options = list(
                range(1, 10)
            )

            if i >= self.n:
                target = seq[i - self.n]

                if target in options:
                    options.remove(target)

            seq.append(
                random.choice(options)
            )

        return seq

    # =====================================================
    # 키 입력
    # =====================================================

    def _on_left(self, _event):
        self.answer(True)

    def _on_right(self, _event):
        self.answer(False)

    # =====================================================
    # 자극 진행
    # =====================================================

    def next_item(self):
        if self.finished:
            return

        self._cancel_trial_timers()

        self.index += 1

        if self.index >= self.rounds:
            self.finish_round()
            return

        # 새 자극임을 확실하게 느끼도록 잠깐 숫자를 비운다.
        self.awaiting = False
        self._set_buttons(False)

        self.stim.config(
            text=""
        )
        self.feedback.config(
            text=""
        )

        self.progress[
            "value"
        ] = self.index + 1

        self.round_label.config(
            text=(
                f"자극 {self.index + 1} / "
                f"{self.rounds}"
            )
        )

        self.timer_label.config(
            text="새 숫자 준비"
        )
        self.time_bar[
            "value"
        ] = 0

        self.transition_id = self.safe_after(
            self.STIMULUS_GAP_MS,
            self._show_current_item,
        )

    def _show_current_item(self):
        if self.finished:
            return

        self.transition_id = None

        value = self.sequence[
            self.index
        ]

        self.stim.config(
            text=str(value)
        )

        # 처음 N개 자극은 비교 대상이 아직 없으므로
        # 답을 요구하지 않는다.
        if self.index < self.n:
            self.awaiting = False
            self._set_buttons(False)

            self._start_timer(
                answerable=False
            )

            self.timeout_id = self.safe_after(
                self.interval,
                self._warmup_finished,
            )
            return

        self.current_is_match = (
            value
            == self.sequence[
                self.index - self.n
            ]
        )

        self.awaiting = True
        self._set_buttons(True)

        self._start_timer(
            answerable=True
        )

        self.timeout_id = self.safe_after(
            self.interval,
            self._timeout_current,
        )

    def _warmup_finished(self):
        self.timeout_id = None

        if self.finished:
            return

        self._stop_timer_display(
            text="다음 숫자"
        )

        self.safe_after(
            20,
            self.next_item,
        )

    # =====================================================
    # 제한시간 표시
    # =====================================================

    def _start_timer(self, answerable):
        self._cancel_timer_tick()

        self.timer_answerable = answerable
        self.timer_started_at = (
            time.perf_counter()
        )

        self.time_bar[
            "value"
        ] = 1000

        self.time_bar.config(
            style=(
                "NBackTimeGood."
                "Horizontal.TProgressbar"
            )
        )

        self._update_timer_display()

    def _update_timer_display(self):
        if (
            self.finished
            or self.timer_started_at is None
        ):
            return

        elapsed = (
            time.perf_counter()
            - self.timer_started_at
        )

        remaining = max(
            0.0,
            self.timer_duration_sec
            - elapsed,
        )

        fraction = (
            remaining
            / self.timer_duration_sec
        )

        self.time_bar[
            "value"
        ] = int(
            fraction * 1000
        )

        if fraction > 0.50:
            bar_style = (
                "NBackTimeGood."
                "Horizontal.TProgressbar"
            )
        elif fraction > 0.25:
            bar_style = (
                "NBackTimeWarn."
                "Horizontal.TProgressbar"
            )
        else:
            bar_style = (
                "NBackTimeDanger."
                "Horizontal.TProgressbar"
            )

        self.time_bar.config(
            style=bar_style
        )

        if self.timer_answerable:
            prefix = "응답 제한시간"
        else:
            prefix = "다음 숫자까지"

        self.timer_label.config(
            text=(
                f"{prefix}  "
                f"{remaining:.1f}초"
            )
        )

        if remaining > 0:
            self.timer_tick_id = (
                self.safe_after(
                    self.TIMER_REFRESH_MS,
                    self._update_timer_display,
                )
            )
        else:
            self.timer_tick_id = None

    def _stop_timer_display(
        self,
        text=None,
    ):
        self._cancel_timer_tick()

        self.timer_started_at = None
        self.time_bar[
            "value"
        ] = 0

        if text is not None:
            self.timer_label.config(
                text=text
            )

    # =====================================================
    # 응답 처리
    # =====================================================

    def answer(self, same):
        if (
            self.finished
            or not self.awaiting
        ):
            return

        self.awaiting = False
        self._set_buttons(False)

        if self.timeout_id is not None:
            self.cancel_after(
                self.timeout_id
            )
            self.timeout_id = None

        self._stop_timer_display(
            text="응답 완료"
        )

        if same == self.current_is_match:
            self.correct += 1

            self.feedback.config(
                text="정답"
            )
        else:
            self.feedback.config(
                text="오답"
            )

        self.safe_after(
            self.ANSWER_FEEDBACK_MS,
            self.next_item,
        )

    def _timeout_current(self):
        self.timeout_id = None

        if self.finished:
            return

        if self.awaiting:
            self.awaiting = False
            self._set_buttons(False)

            self.feedback.config(
                text="시간 초과"
            )

        self._stop_timer_display(
            text="응답 제한시간  0.0초"
        )

        self.safe_after(
            self.ANSWER_FEEDBACK_MS,
            self.next_item,
        )

    # =====================================================
    # 타이머 정리
    # =====================================================

    def _cancel_timer_tick(self):
        if self.timer_tick_id is not None:
            self.cancel_after(
                self.timer_tick_id
            )
            self.timer_tick_id = None

    def _cancel_trial_timers(self):
        if self.timeout_id is not None:
            self.cancel_after(
                self.timeout_id
            )
            self.timeout_id = None

        if self.transition_id is not None:
            self.cancel_after(
                self.transition_id
            )
            self.transition_id = None

        self._cancel_timer_tick()

        self.timer_started_at = None

    def _set_buttons(self, enabled):
        state = (
            "normal"
            if enabled
            else "disabled"
        )

        self.same_btn.config(
            state=state
        )
        self.diff_btn.config(
            state=state
        )

    # =====================================================
    # 라운드 종료
    # =====================================================

    def finish_round(self):
        if self.finished:
            return

        self.finished = True
        self._cancel_trial_timers()
        self.clear_afters()

        try:
            self.unbind_all(
                "<Left>"
            )
            self.unbind_all(
                "<Right>"
            )
        except tk.TclError:
            pass

        total = self.total_answerable

        accuracy = (
            self.correct
            / total
        )

        score = int(
            1000
            * accuracy
            * (
                1
                + 0.18
                * (
                    self.n - 1
                )
            )
            * (
                1
                + self.difficulty
                * 0.05
            )
        )

        self.host.finish(
            RoundResult(
                score=score,
                correct=self.correct,
                total=total,
                accuracy=accuracy,
                duration=self.elapsed(),
                detail=(
                    f"{self.n}-back · "
                    f"제한시간 "
                    f"{self.interval / 1000:.1f}초"
                ),
            )
        )