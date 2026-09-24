from contextlib import asynccontextmanager
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
import urllib.parse

from database import create_db_and_tables, get_session
from models import Reservation

# 설정 상수
ROOMS = [
    {"name": "대회의실", "capacity": "12인실", "desc": "화상회의 장비, 빔프로젝터", "color": "blue"},
    {"name": "미팅룸A", "capacity": "8인실", "desc": "TV 모니터, 대형 화이트보드", "color": "emerald"},
    {"name": "미팅룸B", "capacity": "6인실", "desc": "TV 모니터, 이동식 화이트보드", "color": "violet"},
    {"name": "포커스룸", "capacity": "4인실", "desc": "집중 1:1 면담 및 소규모 회의", "color": "amber"},
]

ROOM_NAMES = [r["name"] for r in ROOMS]
HOURS = list(range(9, 18))  # 9시부터 17시 시작 슬롯 (9:00 ~ 18:00)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 DB 테이블 자동 생성
    create_db_and_tables()
    yield


app = FastAPI(
    title="사내 회의실 예약 시스템",
    description="FastAPI, SQLModel, Jinja2, TailwindCSS 기반의 실시간 사내 회의실 예약 대시보드",
    version="1.0.0",
    lifespan=lifespan
)

# 템플릿 설정
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    session: Session = Depends(get_session),
    success_msg: Optional[str] = None,
    error_msg: Optional[str] = None,
    selected_room: Optional[str] = None,
    selected_time: Optional[int] = None,
):
    # 모든 예약 정보 조회
    statement = select(Reservation).order_by(Reservation.start_time)
    reservations = session.exec(statement).all()

    # 현황판 Grid 매핑: {room_name: {hour: Reservation or None}}
    grid_data: Dict[str, Dict[int, Optional[Reservation]]] = {
        room["name"]: {hour: None for hour in HOURS} for room in ROOMS
    }

    # 전체 예약 통계 계산
    total_slots = len(ROOMS) * len(HOURS)
    booked_slots = 0

    for res in reservations:
        if res.room_name in grid_data and res.start_time in grid_data[res.room_name]:
            grid_data[res.room_name][res.start_time] = res
            booked_slots += 1

    available_slots = total_slots - booked_slots
    utilization_rate = round((booked_slots / total_slots * 100) if total_slots > 0 else 0, 1)

    context = {
        "request": request,
        "rooms": ROOMS,
        "hours": HOURS,
        "grid_data": grid_data,
        "reservations": reservations,
        "total_slots": total_slots,
        "booked_slots": booked_slots,
        "available_slots": available_slots,
        "utilization_rate": utilization_rate,
        "success_msg": success_msg,
        "error_msg": error_msg,
        "selected_room": selected_room,
        "selected_time": selected_time,
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )


@app.post("/reserve")
async def reserve_room(
    reserver_name: str = Form(...),
    room_name: str = Form(...),
    start_time: int = Form(...),
    session: Session = Depends(get_session),
):
    reserver_name = reserver_name.strip()

    # 1. 입력값 기본 유효성 검사
    if not reserver_name:
        err = urllib.parse.quote("예약자 이름을 올바르게 입력해주세요.")
        return RedirectResponse(url=f"/?error_msg={err}", status_code=status.HTTP_303_SEE_OTHER)

    if room_name not in ROOM_NAMES:
        err = urllib.parse.quote("존재하지 않는 회의실입니다.")
        return RedirectResponse(url=f"/?error_msg={err}", status_code=status.HTTP_303_SEE_OTHER)

    if start_time not in HOURS:
        err = urllib.parse.quote("예약 가능한 시간은 9시부터 17시(종료 18시)까지입니다.")
        return RedirectResponse(url=f"/?error_msg={err}", status_code=status.HTTP_303_SEE_OTHER)

    # 2. 중복 예약 검증
    statement = select(Reservation).where(
        Reservation.room_name == room_name,
        Reservation.start_time == start_time
    )
    existing_reservation = session.exec(statement).first()

    if existing_reservation:
        err = urllib.parse.quote(
            f"이미 예약된 시간입니다! ({existing_reservation.room_name} {existing_reservation.start_time}:00~{existing_reservation.end_time}:00 - 예약자: {existing_reservation.reserver_name})"
        )
        return RedirectResponse(
            url=f"/?error_msg={err}&selected_room={urllib.parse.quote(room_name)}&selected_time={start_time}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    # 3. 예약 생성 및 저장
    new_reservation = Reservation(
        reserver_name=reserver_name,
        room_name=room_name,
        start_time=start_time,
        end_time=start_time + 1
    )
    session.add(new_reservation)
    session.commit()
    session.refresh(new_reservation)

    msg = urllib.parse.quote(
        f"'{room_name}' {start_time}:00 ~ {start_time+1}:00 ({reserver_name}님) 예약이 성공적으로 완료되었습니다."
    )
    return RedirectResponse(url=f"/?success_msg={msg}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/cancel/{reservation_id}")
async def cancel_reservation(
    reservation_id: int,
    session: Session = Depends(get_session)
):
    """예약 취소 기능"""
    reservation = session.get(Reservation, reservation_id)
    if not reservation:
        err = urllib.parse.quote("해당 예약 정보를 찾을 수 없습니다.")
        return RedirectResponse(url=f"/?error_msg={err}", status_code=status.HTTP_303_SEE_OTHER)

    room_name = reservation.room_name
    start_time = reservation.start_time
    reserver_name = reservation.reserver_name

    session.delete(reservation)
    session.commit()

    msg = urllib.parse.quote(
        f"'{room_name}' {start_time}:00 ~ {start_time+1}:00 ({reserver_name}님) 예약이 취소되었습니다."
    )
    return RedirectResponse(url=f"/?success_msg={msg}", status_code=status.HTTP_303_SEE_OTHER)
