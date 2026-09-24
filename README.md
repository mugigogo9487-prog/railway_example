# 🏢 사내 회의실 예약 시스템 (Smart Meeting Room Hub)

FastAPI와 SQLModel, Jinja2, TailwindCSS를 활용하여 구축한 **실시간 사내 회의실 예약 및 현황 대시보드 시스템**입니다.

---

## 🌟 주요 기능

1. **실시간 현황 대시보드 (`GET /`)**
   - 09:00부터 18:00까지(1시간 단위) 각 회의실별 예약 현황을 한눈에 파악하는 **인터랙티브 Grid 시간표**.
   - 상단 실시간 통계 KPI (운영 회의실 수, 예약 건수, 잔여 슬롯, 예약 가동률).
   - 예약된 슬롯은 회의실 고유 테마 컬러로 예약자명 및 시간 표시.
   - 빈 슬롯 클릭 시 좌측 폼에 회의실 및 시간이 자동으로 설정되는 **원클릭 자동 완성(Quick Fill)** 지원.

2. **안전한 예약 등록 및 중복 방지 (`POST /reserve`)**
   - 예약자 성명/팀명, 회의실, 시작 시간 선택.
   - **중복 예약 원천 차단**: 동일 회의실 & 동일 시간에 이미 예약이 존재하면 직관적인 에러 알림 제공.
   - 1회 1시간 단위 자동 고정 (`end_time = start_time + 1`).

3. **간편 예약 취소 (`POST /cancel/{id}`)**
   - 타임테이블의 카드 또는 하단 목록에서 손쉽게 예약 취소 가능 (확인 대화상자 지원).

4. **클라우드 배포 지원**
   - `DATABASE_URL` 환경 변수 우선 연동 (Railway/Render의 PostgreSQL 및 로컬 SQLite 자동 감지 및 변환).
   - `Procfile` 및 `runtime.txt` 포함.

---

## 🛠 기술 스택

- **언어**: Python 3.12+
- **패키지 & 프로젝트 관리**: [uv](https://github.com/astral-sh/uv)
- **웹 프레임워크**: [FastAPI](https://fastapi.tiangolo.com/)
- **ORM / 데이터베이스**: [SQLModel](https://sqlmodel.tiangolo.com/) (SQLite 개발용 / PostgreSQL 배포용)
- **템플릿 엔진**: [Jinja2](https://jinja.palletsprojects.com/)
- **스타일링**: [TailwindCSS (CDN)](https://tailwindcss.com/) & FontAwesome Icons

---

## 📁 프로젝트 구조

```
ch10/
├── database.py         # DB 연결 설정 (SQLite/PostgreSQL 분기 및 세션 제공)
├── models.py           # SQLModel Reservation 테이블 모델 정의
├── main.py             # FastAPI 라우터 및 비즈니스 로직
├── templates/
│   ├── base.html       # 공통 레이아웃 (헤더, 시계, 푸터, Tailwind CDN)
│   └── index.html      # 예약 폼 + 실시간 시간표 Grid + 통계 대시보드
├── Procfile            # 클라우드 배포 실행 명령 (Railway 등)
├── runtime.txt         # Python 런타임 버전 지정
├── pyproject.toml      # uv 프로젝트 설정 및 의존성
├── requirements.txt    # 배포용 의존성 목록
├── .env.example        # 환경 변수 예시
└── README.md           # 프로젝트 문서
```

---

## 🚀 로컬 실행 방법

### 1. `uv`를 사용한 실행 (권장)

```bash
# 가상환경 생성 및 의존성 설치 (최초 1회)
uv sync

# 서버 실행 (개발 모드, Hot Reload 지원)
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

브라우저에서 `http://127.0.0.1:8000`에 접속하면 예약 대시보드를 바로 이용할 수 있습니다.

### 2. 일반 `pip`를 사용한 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🌐 클라우드 배포 가이드 (Railway / Render)

1. **GitHub 저장소에 소스코드 푸시**
2. **Railway 또는 Render에서 New Project 생성 후 Repo 연결**
3. **PostgreSQL 데이터베이스 생성 및 연결**:
   - Railway/Render에서 제공하는 `DATABASE_URL` 환경 변수가 자동으로 주입됩니다.
   - `database.py`에서 `DATABASE_URL`이 있으면 PostgreSQL로 자동 연결되며, `postgres://` 접두사도 `postgresql://`로 안전하게 변환됩니다.
4. **빌드 & 실행**:
   - `Procfile`의 `web: uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}` 명령으로 자동 실행됩니다.
