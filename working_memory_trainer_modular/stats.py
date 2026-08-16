import json
from datetime import datetime
from pathlib import Path

from config import (
    MODE_LABELS,
    MIN_DIFFICULTY,
    MAX_DIFFICULTY,
)


class StatsStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _default(self):
        return {
            "total_games": 0,
            "total_score": 0,
            "best_score": 0,
            "mode_best": {
                key: 0
                for key in MODE_LABELS
                if key != "random"
            },
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
                json.dump(
                    self.data,
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

    def add_result(self, mode, result, difficulty):
        self.data["total_games"] += 1
        self.data["total_score"] += result.score
        self.data["best_score"] = max(
            self.data["best_score"],
            result.score,
        )

        if mode in self.data["mode_best"]:
            self.data["mode_best"][mode] = max(
                self.data["mode_best"][mode],
                result.score,
            )

        self.data["history"].append(
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "mode": mode,
                "score": result.score,
                "correct": result.correct,
                "total": result.total,
                "accuracy": round(result.accuracy, 4),
                "duration": round(result.duration, 1),
                "difficulty": difficulty,
                "detail": result.detail,
            }
        )

        self.data["history"] = self.data["history"][-100:]
        self.save()

    def get_difficulty(self, mode):
        return int(self.data["difficulty"].get(mode, 1))

    def set_difficulty(self, mode, value):
        self.data["difficulty"][mode] = max(
            MIN_DIFFICULTY,
            min(MAX_DIFFICULTY, int(value)),
        )
        self.save()

    def reset(self):
        self.data = self._default()
        self.save()
