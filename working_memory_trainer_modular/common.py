import time
from dataclasses import dataclass
from tkinter import ttk


@dataclass
class RoundResult:
    score: int
    correct: int
    total: int
    accuracy: float
    duration: float
    detail: str = ""


class BaseGame(ttk.Frame):
    """
    각 게임이 공통으로 사용하는 기반 클래스.

    게임 파일에서는:
      - BaseGame을 상속
      - host.finish(RoundResult(...)) 로 라운드를 종료
      - 타이머는 self.safe_after(...) 사용
    """

    def __init__(self, host, parent, difficulty):
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

    def cancel_after(self, aid):
        if aid is None:
            return

        try:
            self.after_cancel(aid)
        except Exception:
            pass

        try:
            self.after_ids.remove(aid)
        except ValueError:
            pass

    def clear_afters(self):
        for aid in list(self.after_ids):
            try:
                self.after_cancel(aid)
            except Exception:
                pass

        self.after_ids.clear()

    def destroy(self):
        self.clear_afters()
        super().destroy()

    def elapsed(self):
        return time.time() - self.started_at
