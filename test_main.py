import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from database import get_session
from models import Reservation

# 테스트용 인메모리 SQLite DB 생성
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_get_main_dashboard(client: TestClient):
    """메인 현황판 GET / 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    assert "사내 회의실 예약 시스템" in response.text
    assert "대회의실" in response.text
    assert "미팅룸A" in response.text


def test_reserve_success(client: TestClient):
    """예약 성공 테스트"""
    data = {
        "reserver_name": "홍길동 (개발팀)",
        "room_name": "대회의실",
        "start_time": 10
    }
    response = client.post("/reserve", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert "success_msg" in response.headers["location"]

    # 대시보드에서 예약 확인
    dashboard_res = client.get("/")
    assert "홍길동 (개발팀)" in dashboard_res.text


def test_reserve_duplicate_prevention(client: TestClient):
    """중복 예약 방지 검증 테스트"""
    data1 = {
        "reserver_name": "이순신",
        "room_name": "미팅룸A",
        "start_time": 14
    }
    res1 = client.post("/reserve", data=data1, follow_redirects=False)
    assert res1.status_code == 303
    assert "success_msg" in res1.headers["location"]

    # 동일한 회의실 및 동일 시간에 중복 예약 시도
    data2 = {
        "reserver_name": "강감찬",
        "room_name": "미팅룸A",
        "start_time": 14
    }
    res2 = client.post("/reserve", data=data2, follow_redirects=False)
    assert res2.status_code == 303
    assert "error_msg" in res2.headers["location"]


def test_cancel_reservation(client: TestClient, session: Session):
    """예약 취소 테스트"""
    # 예약 사전 생성
    res = Reservation(
        reserver_name="을지문덕",
        room_name="포커스룸",
        start_time=15,
        end_time=16
    )
    session.add(res)
    session.commit()
    session.refresh(res)

    # 취소 요청
    cancel_res = client.post(f"/cancel/{res.id}", follow_redirects=False)
    assert cancel_res.status_code == 303
    assert "success_msg" in cancel_res.headers["location"]

    # DB에서 삭제되었는지 확인
    deleted = session.get(Reservation, res.id)
    assert deleted is None
