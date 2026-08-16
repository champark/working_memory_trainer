import tkinter as tk
from tkinter import ttk, messagebox
import random
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

APP_TITLE = "작업기억 트레이닝"
SAVE_FILE = Path.home() / ".working_memory_trainer_stats.json"

WORDS = [
    "사과", "기차", "바다", "고양이", "시계", "우산", "호랑이", "연필", "구름", "의자",
    "강아지", "산", "달", "별", "책", "나무", "학교", "창문", "모자", "신발",
    "커피", "바람", "노을", "강", "다리", "풍선", "거울", "전화", "열쇠", "가방",
    "비행기", "토끼", "사자", "꽃", "눈", "비", "숲", "섬", "배", "지도",
    "망치", "컵", "접시", "수건", "바구니", "카메라", "피아노", "기타", "드럼", "촛불",
    "벽돌", "문", "계단", "상자", "병", "종이", "편지", "사진", "신문", "라디오",
]

POSITIONS = [
    (0, 0, "왼쪽 위"), (0, 1, "가운데 위"), (0, 2, "오른쪽 위"),
    (1, 0, "왼쪽 가운데"), (1, 1, "정가운데"), (1, 2, "오른쪽 가운데"),
    (2, 0, "왼쪽 아래"), (2, 1, "가운데 아래"), (2, 2, "오른쪽 아래"),
]

MODE_LABELS = {
    "nback": "N-back",
    "updating": "기억 갱신",
    "math_memory": "계산 + 기억",
    "dual": "이중 기억",
    "random": "랜덤 훈련",
}


@dataclass
class RoundResult:
    score: int
    correct: int
    total: int
    accuracy: float
    duration: float
    detail: str = ""


class StatsStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _default(self):
        return {
            "total_games": 0,
            "total_score": 0,
            "best_score": 0,
            "mode_best": {k: 0 for k in MODE_LABELS if k != "random"},
            "history": [],
            "difficulty": {
                "nback": 1,
                "updating": 1,
                "math_memory": 1,
                "dual": 1,
            },
        }

    def _load(self):
        if not self.path.exists():
            return self._default()
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            base = self._default()
            base.update(raw)
            base["difficulty"].update(raw.get("difficulty", {}))
            base["mode_best"].update(raw.get("mode_best", {}))
            return base
        except Exception:
            return self._default()

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_result(self, mode, result: RoundResult, difficulty):
        self.data["total_games"] += 1
        self.data["total_score"] += result.score
        self.data["best_score"] = max(self.data["best_score"], result.score)
        if mode in self.data["mode_best"]:
            self.data["mode_best"][mode] = max(self.data["mode_best"][mode], result.score)
        self.data["history"].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mode": mode,
            "score": result.score,
            "correct": result.correct,
            "total": result.total,
            "accuracy": round(result.accuracy, 4),
            "duration": round(result.duration, 1),
            "difficulty": difficulty,
            "detail": result.detail,
        })
        self.data["history"] = self.data["history"][-100:]
        self.save()

    def get_difficulty(self, mode):
        return int(self.data["difficulty"].get(mode, 1))

    def set_difficulty(self, mode, value):
        self.data["difficulty"][mode] = max(1, min(10, int(value)))
        self.save()


class WorkingMemoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x700")
        self.minsize(760, 620)
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
        style.configure("Title.TLabel", font=("맑은 고딕", 26, "bold"), background="#f5f6fa")
        style.configure("Sub.TLabel", font=("맑은 고딕", 11), background="#f5f6fa", foreground="#555")
        style.configure("Menu.TButton", font=("맑은 고딕", 13, "bold"), padding=14)
        style.configure("Game.TButton", font=("맑은 고딕", 12, "bold"), padding=10)
        style.configure("Card.TFrame", background="white", relief="solid", borderwidth=1)
        style.configure("Card.TLabel", background="white", font=("맑은 고딕", 11))
        style.configure("Big.TLabel", background="white", font=("맑은 고딕", 34, "bold"))

    def swap(self, frame_cls, *args, **kwargs):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_cls(self, *args, **kwargs)
        self.current_frame.pack(fill="both", expand=True)

    def show_menu(self):
        self.swap(MenuFrame)

    def start_mode(self, mode, random_session=False):
        if mode == "random":
            chosen = random.choice(["nback", "updating", "math_memory", "dual"])
            self.swap(GameHost, chosen, True)
        else:
            self.swap(GameHost, mode, random_session)

    def show_stats(self):
        self.swap(StatsFrame)


class MenuFrame(ttk.Frame):
    def __init__(self, app: WorkingMemoryApp):
        super().__init__(app)
        self.app = app
        self.configure(padding=30)

        ttk.Label(self, text="작업기억 트레이닝", style="Title.TLabel").pack(pady=(15, 6))
        ttk.Label(
            self,
            text="기억을 유지하면서 비교·갱신·계산·조작하는 훈련 모음",
            style="Sub.TLabel"
        ).pack(pady=(0, 25))

        grid = ttk.Frame(self)
        grid.pack(expand=True)
        buttons = [
            ("🔢  N-back", "nback", "몇 단계 전의 자극과 현재 자극을 비교"),
            ("🔄  기억 갱신", "updating", "기억 목록의 특정 항목을 계속 교체"),
            ("🧮  계산 + 기억", "math_memory", "계산을 하면서 단어 순서를 함께 유지"),
            ("🧠  이중 기억", "dual", "숫자와 위치를 동시에 기억"),
            ("🎯  랜덤 훈련", "random", "네 가지 훈련 중 하나를 무작위 선택"),
        ]
        for i, (title, mode, desc) in enumerate(buttons):
            card = ttk.Frame(grid, style="Card.TFrame", padding=16)
            card.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="nsew")
            ttk.Button(card, text=title, style="Menu.TButton",
                       command=lambda m=mode: app.start_mode(m)).pack(fill="x")
            ttk.Label(card, text=desc, style="Card.TLabel", wraplength=300).pack(pady=(8, 0))

        for c in range(2):
            grid.columnconfigure(c, weight=1)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(22, 5))
        ttk.Button(bottom, text="📊 기록 보기", command=app.show_stats).pack(side="left")
        ttk.Button(bottom, text="종료", command=app.destroy).pack(side="right")


class GameHost(ttk.Frame):
    def __init__(self, app: WorkingMemoryApp, mode: str, random_session=False):
        super().__init__(app)
        self.app = app
        self.mode = mode
        self.random_session = random_session
        self.configure(padding=20)
        self.game = None

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Button(header, text="← 메뉴", command=app.show_menu).pack(side="left")
        title = MODE_LABELS[mode]
        if random_session:
            title = f"랜덤 훈련 · {title}"
        ttk.Label(header, text=title, font=("맑은 고딕", 20, "bold")).pack(side="left", padx=18)
        self.diff_label = ttk.Label(header, text="")
        self.diff_label.pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=12)
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)

        self.start_game()

    def start_game(self):
        difficulty = self.app.stats.get_difficulty(self.mode)
        self.diff_label.config(text=f"자동 난이도 {difficulty}")
        cls = {
            "nback": NBackGame,
            "updating": UpdatingGame,
            "math_memory": MathMemoryGame,
            "dual": DualMemoryGame,
        }[self.mode]
        self.game = cls(self, self.body, difficulty)
        self.game.pack(fill="both", expand=True)

    def finish(self, result: RoundResult):
        old_diff = self.app.stats.get_difficulty(self.mode)
        new_diff = old_diff
        if result.total >= 3:
            if result.accuracy >= 0.85:
                new_diff = min(10, old_diff + 1)
            elif result.accuracy < 0.60:
                new_diff = max(1, old_diff - 1)
        self.app.stats.set_difficulty(self.mode, new_diff)
        self.app.stats.add_result(self.mode, result, old_diff)

        if self.game:
            self.game.destroy()
        ResultPanel(self, self.body, result, self.mode, old_diff, new_diff, self.random_session).pack(
            fill="both", expand=True
        )


class BaseGame(ttk.Frame):
    def __init__(self, host: GameHost, parent, difficulty):
        super().__init__(parent)
        self.host = host
        self.app = host.app
        self.difficulty = difficulty
        self.started_at = time.time()
        self.after_ids = []

    def safe_after(self, ms, func):
        aid = self.after(ms, func)
        self.after_ids.append(aid)
        return aid

    def destroy(self):
        for aid in self.after_ids:
            try:
                self.after_cancel(aid)
            except Exception:
                pass
        super().destroy()

    def elapsed(self):
        return time.time() - self.started_at


class NBackGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)
        self.n = min(4, 1 + (difficulty - 1) // 3)
        self.rounds = 10 + difficulty * 2
        self.interval = max(900, 1900 - difficulty * 90)
        self.sequence = self._make_sequence()
        self.index = -1
        self.correct = 0
        self.answers = 0
        self.awaiting = False
        self.current_is_match = False

        ttk.Label(self, text=f"{self.n}-back: 현재 숫자가 {self.n}칸 전 숫자와 같은지 판단하세요.",
                  font=("맑은 고딕", 13)).pack(pady=(10, 12))
        self.progress = ttk.Progressbar(self, maximum=self.rounds, length=500)
        self.progress.pack(pady=8)
        card = ttk.Frame(self, style="Card.TFrame", padding=35)
        card.pack(expand=True, fill="both", padx=70, pady=15)
        self.stim = ttk.Label(card, text="준비", style="Big.TLabel", anchor="center")
        self.stim.pack(expand=True)
        self.feedback = ttk.Label(card, text="", style="Card.TLabel")
        self.feedback.pack(pady=5)

        buttons = ttk.Frame(self)
        buttons.pack(pady=14)
        self.same_btn = ttk.Button(buttons, text="같다  [←]", style="Game.TButton",
                                   command=lambda: self.answer(True), state="disabled")
        self.same_btn.pack(side="left", padx=8)
        self.diff_btn = ttk.Button(buttons, text="다르다  [→]", style="Game.TButton",
                                   command=lambda: self.answer(False), state="disabled")
        self.diff_btn.pack(side="left", padx=8)
        self.bind_all("<Left>", lambda e: self.answer(True))
        self.bind_all("<Right>", lambda e: self.answer(False))
        self.safe_after(900, self.next_item)

    def _make_sequence(self):
        seq = []
        for i in range(self.rounds):
            if i >= self.n and random.random() < 0.38:
                seq.append(seq[i - self.n])
            else:
                options = list(range(1, 10))
                if i >= self.n and seq[i - self.n] in options:
                    options.remove(seq[i - self.n])
                seq.append(random.choice(options))
        return seq

    def next_item(self):
        if self.awaiting:
            self._grade(False, timed_out=True)
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
            self.same_btn.config(state="disabled")
            self.diff_btn.config(state="disabled")
            self.safe_after(self.interval, self.next_item)
            return

        self.current_is_match = value == self.sequence[self.index - self.n]
        self.awaiting = True
        self.same_btn.config(state="normal")
        self.diff_btn.config(state="normal")
        self.safe_after(self.interval, self.next_item)

    def answer(self, same):
        if not self.awaiting:
            return
        self._grade(same)

    def _grade(self, answer, timed_out=False):
        if not self.awaiting:
            return
        self.awaiting = False
        self.answers += 1
        ok = (answer == self.current_is_match) and not timed_out
        if ok:
            self.correct += 1
            self.feedback.config(text="정답")
        else:
            self.feedback.config(text="시간 초과" if timed_out else "오답")
        self.same_btn.config(state="disabled")
        self.diff_btn.config(state="disabled")

    def finish_round(self):
        total = max(1, self.rounds - self.n)
        accuracy = self.correct / total
        score = int(1000 * accuracy * (1 + 0.18 * (self.n - 1)) * (1 + self.difficulty * 0.05))
        self.unbind_all("<Left>")
        self.unbind_all("<Right>")
        self.host.finish(RoundResult(score, self.correct, total, accuracy, self.elapsed(), f"{self.n}-back"))


class UpdatingGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)
        self.slots = min(7, 3 + (difficulty - 1) // 2)
        self.updates_count = 3 + difficulty
        self.display_ms = max(1800, 3800 - difficulty * 140)
        self.memory = random.sample(WORDS, self.slots)
        self.updates = []
        self.step = -1
        self.entry_vars = []

        ttk.Label(self, text="처음 목록을 기억한 뒤, 지시에 따라 머릿속 목록을 계속 갱신하세요.",
                  font=("맑은 고딕", 13)).pack(pady=(10, 8))
        self.progress = ttk.Progressbar(self, maximum=self.updates_count + 1, length=520)
        self.progress.pack(pady=8)
        card = ttk.Frame(self, style="Card.TFrame", padding=30)
        card.pack(expand=True, fill="both", padx=60, pady=15)
        self.main = ttk.Label(card, text="", font=("맑은 고딕", 25, "bold"), background="white",
                              anchor="center", justify="center", wraplength=650)
        self.main.pack(expand=True)
        self.sub = ttk.Label(card, text="", style="Card.TLabel", anchor="center")
        self.sub.pack(pady=8)

        self.safe_after(500, self.show_initial)

    def show_initial(self):
        text = "   ·   ".join(f"{i+1}. {w}" for i, w in enumerate(self.memory))
        self.main.config(text=text)
        self.sub.config(text=f"{self.slots}개 단어를 기억하세요")
        self.progress["value"] = 1
        self.safe_after(self.display_ms + 800, self.prepare_updates)

    def prepare_updates(self):
        used_recent = set(self.memory)
        for _ in range(self.updates_count):
            idx = random.randrange(self.slots)
            choices = [w for w in WORDS if w not in used_recent]
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
        self.main.config(text=f"{idx + 1}번째 단어를\n\n‘{word}’(으)로 변경")
        self.sub.config(text=f"갱신 {self.step + 1} / {self.updates_count}")
        self.progress["value"] = self.step + 2
        self.step += 1
        self.safe_after(self.display_ms, self.show_update)

    def show_recall(self):
        self.main.pack_forget()
        self.sub.config(text="현재 기억하고 있는 단어를 순서대로 입력하세요.")
        form = ttk.Frame(self)
        form.pack(expand=True, pady=10)
        for i in range(self.slots):
            row = ttk.Frame(form)
            row.pack(pady=5)
            ttk.Label(row, text=f"{i+1}번", width=6).pack(side="left")
            var = tk.StringVar()
            ent = ttk.Entry(row, textvariable=var, width=24, font=("맑은 고딕", 12))
            ent.pack(side="left")
            self.entry_vars.append(var)
            if i == 0:
                ent.focus_set()
        ttk.Button(form, text="채점", style="Game.TButton", command=self.grade).pack(pady=14)

    def grade(self):
        answers = [v.get().strip() for v in self.entry_vars]
        correct = sum(a == b for a, b in zip(answers, self.memory))
        total = self.slots
        accuracy = correct / total
        score = int(1000 * accuracy * (1 + self.slots * 0.06) * (1 + self.updates_count * 0.035))
        self.host.finish(RoundResult(score, correct, total, accuracy, self.elapsed(),
                                     f"{self.slots}칸 · {self.updates_count}회 갱신"))


class MathMemoryGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)
        self.rounds = min(10, 4 + difficulty // 2)
        self.math_level = 1 + (difficulty - 1) // 3
        self.word_ms = max(1000, 2300 - difficulty * 100)
        self.index = 0
        self.words = random.sample(WORDS, self.rounds)
        self.correct_math = 0
        self.correct_words = 0
        self.current_answer = None
        self.word_entries = []

        ttk.Label(self, text="계산 문제를 풀고, 직후 나타나는 단어도 순서대로 기억하세요.",
                  font=("맑은 고딕", 13)).pack(pady=(10, 10))
        self.progress = ttk.Progressbar(self, maximum=self.rounds, length=520)
        self.progress.pack(pady=6)
        card = ttk.Frame(self, style="Card.TFrame", padding=35)
        card.pack(expand=True, fill="both", padx=70, pady=15)
        self.main = ttk.Label(card, text="", style="Big.TLabel", anchor="center")
        self.main.pack(expand=True)
        self.info = ttk.Label(card, text="", style="Card.TLabel")
        self.info.pack()
        self.answer_var = tk.StringVar()
        self.entry = ttk.Entry(card, textvariable=self.answer_var, width=12, font=("맑은 고딕", 16), justify="center")
        self.entry.pack(pady=12)
        self.entry.bind("<Return>", lambda e: self.submit_math())
        self.submit_btn = ttk.Button(card, text="정답 입력", command=self.submit_math)
        self.submit_btn.pack()
        self.safe_after(500, self.next_math)

    def make_problem(self):
        if self.math_level == 1:
            a, b = random.randint(2, 20), random.randint(2, 12)
            if random.random() < 0.5:
                return f"{a} + {b} = ?", a + b
            if b > a:
                a, b = b, a
            return f"{a} - {b} = ?", a - b
        if self.math_level == 2:
            typ = random.choice(["+", "-", "×"])
            if typ == "×":
                a, b = random.randint(2, 12), random.randint(2, 9)
                return f"{a} × {b} = ?", a * b
            a, b = random.randint(10, 60), random.randint(3, 30)
            if typ == "+":
                return f"{a} + {b} = ?", a + b
            if b > a:
                a, b = b, a
            return f"{a} - {b} = ?", a - b
        typ = random.choice(["+", "-", "×", "mix"])
        if typ == "mix":
            a, b, c = random.randint(10, 40), random.randint(2, 9), random.randint(2, 8)
            return f"{a} + {b} × {c} = ?", a + b * c
        if typ == "×":
            a, b = random.randint(4, 18), random.randint(3, 12)
            return f"{a} × {b} = ?", a * b
        a, b = random.randint(20, 100), random.randint(5, 50)
        if typ == "+":
            return f"{a} + {b} = ?", a + b
        if b > a:
            a, b = b, a
        return f"{a} - {b} = ?", a - b

    def next_math(self):
        if self.index >= self.rounds:
            self.show_word_recall()
            return
        question, ans = self.make_problem()
        self.current_answer = ans
        self.progress["value"] = self.index
        self.main.config(text=question)
        self.info.config(text=f"문제 {self.index + 1} / {self.rounds}")
        self.answer_var.set("")
        self.entry.config(state="normal")
        self.submit_btn.config(state="normal")
        self.entry.focus_set()

    def submit_math(self):
        if self.entry["state"] == "disabled":
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
        for child in self.winfo_children():
            child.destroy()
        ttk.Label(self, text="지금까지 나타난 단어를 순서대로 입력하세요.",
                  font=("맑은 고딕", 14, "bold")).pack(pady=12)
        form = ttk.Frame(self)
        form.pack(expand=True)
        for i in range(self.rounds):
            row = ttk.Frame(form)
            row.pack(pady=3)
            ttk.Label(row, text=f"{i+1}.", width=4).pack(side="left")
            var = tk.StringVar()
            ent = ttk.Entry(row, textvariable=var, width=22)
            ent.pack(side="left")
            self.word_entries.append(var)
            if i == 0:
                ent.focus_set()
        ttk.Button(self, text="채점", style="Game.TButton", command=self.grade).pack(pady=16)

    def grade(self):
        answers = [v.get().strip() for v in self.word_entries]
        self.correct_words = sum(a == b for a, b in zip(answers, self.words))
        total = self.rounds * 2
        correct = self.correct_math + self.correct_words
        accuracy = correct / total
        memory_acc = self.correct_words / self.rounds
        score = int(1000 * accuracy * (1 + self.math_level * 0.08) * (1 + self.rounds * 0.035))
        detail = f"계산 {self.correct_math}/{self.rounds}, 단어 {self.correct_words}/{self.rounds}"
        self.host.finish(RoundResult(score, correct, total, accuracy, self.elapsed(), detail))


class DualMemoryGame(BaseGame):
    def __init__(self, host, parent, difficulty):
        super().__init__(host, parent, difficulty)
        self.items = min(8, 3 + (difficulty - 1) // 2)
        self.digits = min(4, 2 + (difficulty - 1) // 4)
        self.display_ms = max(1200, 2600 - difficulty * 110)
        self.sequence = []
        self.index = 0
        self.entries = []

        for _ in range(self.items):
            low = 10 ** (self.digits - 1)
            high = 10 ** self.digits - 1
            number = random.randint(low, high)
            pos = random.choice(POSITIONS)
            self.sequence.append((number, pos))

        ttk.Label(self, text="숫자와 표시 위치를 한 쌍으로 기억하세요.", font=("맑은 고딕", 13)).pack(pady=(8, 8))
        self.progress = ttk.Progressbar(self, maximum=self.items, length=520)
        self.progress.pack(pady=6)

        self.board = tk.Frame(self, bg="white", highlightthickness=1, highlightbackground="#aaa", width=460, height=360)
        self.board.pack(expand=True, pady=12)
        self.board.pack_propagate(False)
        self.cells = {}
        for r in range(3):
            self.board.grid_rowconfigure(r, weight=1, uniform="r")
            self.board.grid_columnconfigure(r, weight=1, uniform="c")
            for c in range(3):
                cell = tk.Label(self.board, text="", bg="white", font=("맑은 고딕", 22, "bold"),
                                relief="solid", borderwidth=1)
                cell.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                self.cells[(r, c)] = cell
        self.info = ttk.Label(self, text="")
        self.info.pack(pady=5)
        self.safe_after(600, self.show_item)

    def show_item(self):
        if self.index >= self.items:
            self.show_recall()
            return
        for cell in self.cells.values():
            cell.config(text="", bg="white")
        num, (r, c, label) = self.sequence[self.index]
        self.cells[(r, c)].config(text=str(num), bg="#fff3b0")
        self.info.config(text=f"{self.index + 1} / {self.items}")
        self.progress["value"] = self.index + 1
        self.index += 1
        self.safe_after(self.display_ms, self.show_item)

    def show_recall(self):
        for child in self.winfo_children():
            child.destroy()
        ttk.Label(self, text="각 순서의 숫자와 위치를 입력하세요.", font=("맑은 고딕", 14, "bold")).pack(pady=10)
        ttk.Label(self, text="위치는 목록에서 선택합니다. 숫자와 위치를 각각 채점합니다.").pack(pady=(0, 8))
        form = ttk.Frame(self)
        form.pack(expand=True)
        pos_names = [p[2] for p in POSITIONS]
        for i in range(self.items):
            row = ttk.Frame(form)
            row.pack(pady=4)
            ttk.Label(row, text=f"{i+1}번", width=5).pack(side="left")
            nvar = tk.StringVar()
            pvar = tk.StringVar()
            ent = ttk.Entry(row, textvariable=nvar, width=12)
            ent.pack(side="left", padx=5)
            combo = ttk.Combobox(row, textvariable=pvar, values=pos_names, state="readonly", width=16)
            combo.pack(side="left", padx=5)
            self.entries.append((nvar, pvar))
            if i == 0:
                ent.focus_set()
        ttk.Button(self, text="채점", style="Game.TButton", command=self.grade).pack(pady=14)

    def grade(self):
        correct_num = 0
        correct_pos = 0
        for (nvar, pvar), (number, pos) in zip(self.entries, self.sequence):
            if nvar.get().strip() == str(number):
                correct_num += 1
            if pvar.get().strip() == pos[2]:
                correct_pos += 1
        correct = correct_num + correct_pos
        total = self.items * 2
        accuracy = correct / total
        score = int(1000 * accuracy * (1 + self.digits * 0.08) * (1 + self.items * 0.04))
        detail = f"숫자 {correct_num}/{self.items}, 위치 {correct_pos}/{self.items}"
        self.host.finish(RoundResult(score, correct, total, accuracy, self.elapsed(), detail))


class ResultPanel(ttk.Frame):
    def __init__(self, host, parent, result, mode, old_diff, new_diff, random_session):
        super().__init__(parent)
        self.host = host
        self.app = host.app
        self.mode = mode
        self.random_session = random_session

        ttk.Label(self, text="훈련 완료", font=("맑은 고딕", 24, "bold")).pack(pady=(35, 12))
        card = ttk.Frame(self, style="Card.TFrame", padding=30)
        card.pack(padx=90, pady=10, fill="x")
        ttk.Label(card, text=f"점수  {result.score:,}", font=("맑은 고딕", 25, "bold"), background="white").pack(pady=5)
        ttk.Label(card, text=f"정확도  {result.accuracy*100:.1f}%   ({result.correct}/{result.total})",
                  style="Card.TLabel").pack(pady=4)
        ttk.Label(card, text=f"소요 시간  {result.duration:.1f}초", style="Card.TLabel").pack(pady=4)
        if result.detail:
            ttk.Label(card, text=result.detail, style="Card.TLabel").pack(pady=4)

        if new_diff > old_diff:
            msg = f"정확도가 높아 난이도가 {old_diff} → {new_diff}로 상승했습니다."
        elif new_diff < old_diff:
            msg = f"정확도가 낮아 난이도가 {old_diff} → {new_diff}로 조정되었습니다."
        else:
            msg = f"난이도 {old_diff} 유지"
        ttk.Label(self, text=msg, font=("맑은 고딕", 12)).pack(pady=12)

        if result.accuracy >= 0.9:
            eval_text = "매우 안정적입니다. 다음 난이도에서도 정확도를 유지해 보세요."
        elif result.accuracy >= 0.75:
            eval_text = "좋습니다. 속도보다 정확도를 먼저 유지하는 편이 좋습니다."
        elif result.accuracy >= 0.6:
            eval_text = "적당히 어려운 구간입니다. 같은 유형을 한 번 더 해볼 만합니다."
        else:
            eval_text = "부하가 조금 높았습니다. 난이도가 자동으로 완화됩니다."
        ttk.Label(self, text=eval_text).pack(pady=(0, 18))

        buttons = ttk.Frame(self)
        buttons.pack(pady=8)
        ttk.Button(buttons, text="같은 훈련 다시", style="Game.TButton",
                   command=lambda: self.app.start_mode(self.mode, False)).pack(side="left", padx=7)
        ttk.Button(buttons, text="랜덤 훈련", style="Game.TButton",
                   command=lambda: self.app.start_mode("random")).pack(side="left", padx=7)
        ttk.Button(buttons, text="메뉴", style="Game.TButton", command=self.app.show_menu).pack(side="left", padx=7)


class StatsFrame(ttk.Frame):
    def __init__(self, app: WorkingMemoryApp):
        super().__init__(app)
        self.app = app
        self.configure(padding=24)
        data = app.stats.data

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Button(header, text="← 메뉴", command=app.show_menu).pack(side="left")
        ttk.Label(header, text="훈련 기록", font=("맑은 고딕", 22, "bold")).pack(side="left", padx=16)
        ttk.Button(header, text="기록 초기화", command=self.reset_stats).pack(side="right")

        summary = ttk.Frame(self, style="Card.TFrame", padding=18)
        summary.pack(fill="x", pady=18)
        avg = data["total_score"] / data["total_games"] if data["total_games"] else 0
        ttk.Label(summary, text=f"총 훈련 {data['total_games']}회", style="Card.TLabel").pack(side="left", padx=15)
        ttk.Label(summary, text=f"최고 점수 {data['best_score']:,}", style="Card.TLabel").pack(side="left", padx=15)
        ttk.Label(summary, text=f"평균 점수 {avg:,.0f}", style="Card.TLabel").pack(side="left", padx=15)

        diff_frame = ttk.LabelFrame(self, text="현재 자동 난이도", padding=12)
        diff_frame.pack(fill="x", pady=(0, 14))
        for mode in ["nback", "updating", "math_memory", "dual"]:
            ttk.Label(diff_frame, text=f"{MODE_LABELS[mode]}: {data['difficulty'].get(mode, 1)}").pack(side="left", padx=16)

        columns = ("time", "mode", "score", "accuracy", "difficulty", "detail")
        tree = ttk.Treeview(self, columns=columns, show="headings", height=16)
        tree.heading("time", text="시간")
        tree.heading("mode", text="훈련")
        tree.heading("score", text="점수")
        tree.heading("accuracy", text="정확도")
        tree.heading("difficulty", text="난이도")
        tree.heading("detail", text="상세")
        tree.column("time", width=125, anchor="center")
        tree.column("mode", width=100, anchor="center")
        tree.column("score", width=75, anchor="center")
        tree.column("accuracy", width=75, anchor="center")
        tree.column("difficulty", width=65, anchor="center")
        tree.column("detail", width=220, anchor="w")
        tree.pack(fill="both", expand=True)

        for item in reversed(data["history"][-50:]):
            tree.insert("", "end", values=(
                item.get("time", ""),
                MODE_LABELS.get(item.get("mode"), item.get("mode", "")),
                f"{item.get('score', 0):,}",
                f"{item.get('accuracy', 0)*100:.1f}%",
                item.get("difficulty", 1),
                item.get("detail", ""),
            ))

    def reset_stats(self):
        if messagebox.askyesno("기록 초기화", "모든 훈련 기록과 자동 난이도를 초기화할까요?"):
            self.app.stats.data = self.app.stats._default()
            self.app.stats.save()
            self.app.show_stats()


def main():
    app = WorkingMemoryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
