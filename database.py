import os
from sqlmodel import SQLModel, create_engine, Session

# 환경 변수 DATABASE_URL 조회 (없으면 로컬 SQLite 사용)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# PostgreSQL 환경에서 postgres:// 로 시작하는 URL을 postgresql:// 로 변환 (SQLAlchemy 호환성)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite용 연결 옵션
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)


def create_db_and_tables():
    """데이터베이스 및 테이블 생성"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """DB 세션 생성기 (FastAPI Depends 용)"""
    with Session(engine) as session:
        yield session
