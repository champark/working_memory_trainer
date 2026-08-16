from pathlib import Path

APP_TITLE = "작업기억 트레이닝"
WINDOW_SIZE = "900x700"
WINDOW_MIN_SIZE = (760, 620)

SAVE_FILE = Path.home() / ".working_memory_trainer_stats.json"

WORDS = [
    "사과", "기차", "바다", "고양이", "시계", "우산", "호랑이", "연필",
    "구름", "의자", "강아지", "산", "달", "별", "책", "나무",
    "학교", "창문", "모자", "신발", "커피", "바람", "노을", "강",
    "다리", "풍선", "거울", "전화", "열쇠", "가방", "비행기", "토끼",
    "사자", "꽃", "눈", "비", "숲", "섬", "배", "지도",
    "망치", "컵", "접시", "수건", "바구니", "카메라", "피아노",
    "기타", "드럼", "촛불", "벽돌", "문", "계단", "상자", "병",
    "종이", "편지", "사진", "신문", "라디오",
]

POSITIONS = [
    (0, 0, "왼쪽 위"),
    (0, 1, "가운데 위"),
    (0, 2, "오른쪽 위"),
    (1, 0, "왼쪽 가운데"),
    (1, 1, "정가운데"),
    (1, 2, "오른쪽 가운데"),
    (2, 0, "왼쪽 아래"),
    (2, 1, "가운데 아래"),
    (2, 2, "오른쪽 아래"),
]

MODE_LABELS = {
    "nback": "N-back",
    "updating": "기억 갱신",
    "math_memory": "계산 + 기억",
    "dual": "이중 기억",
    "random": "랜덤 훈련",
}

TRAINING_MODES = ("nback", "updating", "math_memory", "dual")

AUTO_DIFFICULTY_UP = 0.85
AUTO_DIFFICULTY_DOWN = 0.60
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 10
