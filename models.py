from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Reservation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reserver_name: str = Field(index=True, description="예약자 이름")
    room_name: str = Field(index=True, description="회의실 이름")
    start_time: int = Field(description="시작 시간 (9~17)")
    end_time: int = Field(description="종료 시간 (start_time + 1)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="예약 생성 일시 (UTC)"
    )
