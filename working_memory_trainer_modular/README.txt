작업기억 트레이닝 - 모듈 분리판
================================

실행 방법
---------
1. 이 폴더의 구조를 그대로 유지합니다.
2. Python 3가 설치되어 있어야 합니다.
3. main.py를 실행합니다.

Windows 명령 프롬프트:
    python main.py

폴더 구조
---------
working_memory_trainer_modular/
│
├─ main.py
├─ config.py
├─ stats.py
├─ common.py
├─ README.txt
└─ games/
    ├─ __init__.py
    ├─ nback.py
    ├─ updating.py
    ├─ math_memory.py
    └─ dual_memory.py

파일 역할
---------
main.py
    메인 창, 메뉴, 게임 전환, 결과 화면, 기록 화면

config.py
    공통 설정, 단어 목록, 위치 목록, 난이도 기준

stats.py
    기록 저장/불러오기, 난이도 저장

common.py
    RoundResult, BaseGame 등 게임 공통 기능

games/nback.py
    N-back 전용 코드

games/updating.py
    기억 갱신 전용 코드

games/math_memory.py
    계산 + 기억 전용 코드

games/dual_memory.py
    이중 기억 전용 코드

새 게임 추가 방법
-----------------
1. games 폴더 안에 새게임.py 생성
2. BaseGame을 상속한 게임 클래스 작성
3. games/__init__.py의 GAME_CLASSES에 등록
4. config.py의 MODE_LABELS / TRAINING_MODES에 등록
5. main.py 메뉴 버튼을 추가

기록 파일
---------
기록은 사용자의 홈 폴더에 아래 파일로 저장됩니다.

    .working_memory_trainer_stats.json

기존 통합판과 같은 저장 위치이므로 기록을 이어서 사용할 수 있습니다.

N-back 변경점
-------------
모듈 분리 작업과 함께 N-back의 타이머 흐름도 정리했습니다.

기존처럼 다음 자극 예약과 응답 타임아웃이 서로 겹치지 않도록,
각 자극마다 하나의 타임아웃만 유지합니다.

흐름:
    자극 표시
      ↓
    응답 대기
      ↓
    응답 또는 시간 초과
      ↓
    다음 자극

따라서 이후 N-back 오류 수정은 주로 games/nback.py만 보면 됩니다.
