from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)

from .db import Base


class Flight(Base):
    """單一日期/機場/方向/航班的目前狀態（每次抓取用 upsert 更新，不逐次累積歷史）。"""

    __tablename__ = "flights"
    __table_args__ = (
        UniqueConstraint("date", "airport", "direction", "flight_no", name="uq_flight_slot"),
    )

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    airport = Column(String(4), nullable=False, index=True)  # LZN / MFK
    direction = Column(String(1), nullable=False)  # D=離站 A=到站
    flight_no = Column(String(20), nullable=False)
    airline = Column(String(50))
    other_airport = Column(String(20))  # 對方站，通常是臺北(松山)
    sched_time = Column(String(5))  # 表定時間 HH:MM
    actual_time = Column(String(5))  # 預定/實際時間 HH:MM
    aircraft_type = Column(String(20))
    terminal = Column(String(20))
    status = Column(String(20))  # 準時/延誤/取消 等原始文字
    fetched_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FerryAnnouncement(Base):
    """matsuebs.com 首頁「最新消息」的原始公告，用關鍵字粗略分類。"""

    __tablename__ = "ferry_announcements"

    id = Column(Integer, primary_key=True)
    news_id = Column(String(30), unique=True, index=True)
    category = Column(String(20))  # 航班公告/系統資訊...
    title = Column(String(255))
    published_date = Column(Date)
    pinned = Column(Boolean, default=False)
    url = Column(String(255))
    parsed_status = Column(String(20))  # cancelled/extra/changed/unknown
    fetched_at = Column(DateTime, server_default=func.now())


class FerrySchedule(Base):
    """每天/每航線的船班狀態，由固定規則產生後再套用公告覆蓋。"""

    __tablename__ = "ferry_schedules"
    __table_args__ = (UniqueConstraint("date", "route", name="uq_ferry_slot"),)

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    route = Column(String(10), nullable=False)  # 南竿 / 東引
    depart_port = Column(String(20), default="基隆")
    arrive_order = Column(String(20))  # 先馬後東 / 先東後馬
    sched_depart_time = Column(String(5), default="22:50")
    status = Column(String(30), default="正常")  # 正常/停航/停航(定期保養)/加班
    note = Column(Text, nullable=True)
    source_url = Column(String(255), nullable=True)


class Advisory(Base):
    """整合提示卡：某天航班/船班異常時產生的建議訊息。"""

    __tablename__ = "advisories"
    __table_args__ = (UniqueConstraint("date", "type", name="uq_advisory_slot"),)

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    type = Column(String(30))  # flight_cancel_wave / ferry_cancel
    message = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Subscription(Base):
    """v1 只建表佔位，尚未開放註冊/發送，供 v2 通知功能使用。"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    channel = Column(String(20))  # email/telegram/line
    target = Column(String(255), nullable=True)
    filter = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
