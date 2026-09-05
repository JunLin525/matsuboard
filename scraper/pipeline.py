"""串起 adapters -> DB 的實際業務邏輯，Lambda handler 跟本機 CLI 都呼叫這裡。"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from common.db import SessionLocal
from common.models import Advisory, FerryAnnouncement, FerrySchedule, Flight

from .adapters.caa_flights import fetch_caa_flights
from .adapters.matsu_ferry import (
    extract_dates_from_title,
    fetch_ferry_announcements,
    ferry_route_order,
)

AIRPORTS = ["LZN", "MFK"]
DIRECTIONS = ["D", "A"]
ROUTES = ["南竿", "東引"]
RETENTION_DAYS = 3
SCHEDULE_HORIZON_DAYS = 3  # 產生今天起 N 天的固定船班骨架


def refresh_flights() -> None:
    """抓南竿/北竿 x 離站/到站，用 upsert 更新今天的航班狀態。"""
    today = date.today()
    db = SessionLocal()
    try:
        for airport in AIRPORTS:
            for direction in DIRECTIONS:
                try:
                    rows = fetch_caa_flights(airport, direction)
                except Exception as exc:  # noqa: BLE001 - 單一來源失敗不該讓整個任務掛掉
                    print(f"[refresh_flights] {airport}/{direction} 抓取失敗: {exc}")
                    continue

                for row in rows:
                    _upsert_flight(db, today, airport, direction, row)
        db.commit()
    finally:
        db.close()


def _upsert_flight(db, today: date, airport: str, direction: str, row: dict) -> None:
    existing = (
        db.query(Flight)
        .filter_by(date=today, airport=airport, direction=direction, flight_no=row["flight_no"])
        .one_or_none()
    )
    if existing:
        existing.airline = row["airline"]
        existing.other_airport = row["other_airport"]
        existing.sched_time = row["sched_time"]
        existing.actual_time = row["actual_time"]
        existing.aircraft_type = row["aircraft_type"]
        existing.terminal = row["terminal"]
        existing.status = row["status"]
        existing.fetched_at = datetime.utcnow()
    else:
        db.add(
            Flight(
                date=today,
                airport=airport,
                direction=direction,
                flight_no=row["flight_no"],
                airline=row["airline"],
                other_airport=row["other_airport"],
                sched_time=row["sched_time"],
                actual_time=row["actual_time"],
                aircraft_type=row["aircraft_type"],
                terminal=row["terminal"],
                status=row["status"],
            )
        )


def refresh_ferry_announcements() -> None:
    db = SessionLocal()
    try:
        try:
            rows = fetch_ferry_announcements()
        except Exception as exc:  # noqa: BLE001
            print(f"[refresh_ferry_announcements] 抓取失敗: {exc}")
            return

        for row in rows:
            existing = db.query(FerryAnnouncement).filter_by(news_id=row["news_id"]).one_or_none()
            if existing:
                existing.category = row["category"]
                existing.title = row["title"]
                existing.published_date = row["published_date"]
                existing.pinned = row["pinned"]
                existing.parsed_status = row["parsed_status"]
            else:
                db.add(FerryAnnouncement(**row))
        db.commit()
    finally:
        db.close()


def sync_ferry_schedule() -> None:
    """先用固定規則(單馬雙東/週二保養)產生骨架，再套用公告裡的停航資訊。"""
    db = SessionLocal()
    try:
        today = date.today()
        for offset in range(SCHEDULE_HORIZON_DAYS):
            _ensure_schedule_rows(db, today + timedelta(days=offset))
        db.flush()

        cancelled_announcements = (
            db.query(FerryAnnouncement).filter(FerryAnnouncement.parsed_status == "cancelled").all()
        )
        for ann in cancelled_announcements:
            for d in extract_dates_from_title(ann.title, today.year):
                for route in ROUTES:
                    sched = db.query(FerrySchedule).filter_by(date=d, route=route).one_or_none()
                    if sched and sched.status == "正常":
                        sched.status = "停航"
                        sched.note = ann.title
                        sched.source_url = ann.url
        db.commit()
    finally:
        db.close()


def _ensure_schedule_rows(db, d: date) -> None:
    is_tuesday = d.weekday() == 1  # 週二固定停航保養
    order = ferry_route_order(d)
    for route in ROUTES:
        existing = db.query(FerrySchedule).filter_by(date=d, route=route).one_or_none()
        if existing:
            continue
        db.add(
            FerrySchedule(
                date=d,
                route=route,
                depart_port="基隆",
                arrive_order=order,
                sched_depart_time="22:50",
                status="停航(定期保養)" if is_tuesday else "正常",
            )
        )


def compute_advisory() -> None:
    """今天某機場航班「全數取消」時，產生建議搭船的提示卡。"""
    today = date.today()
    db = SessionLocal()
    try:
        for airport in AIRPORTS:
            flights_today = db.query(Flight).filter_by(date=today, airport=airport).all()
            if not flights_today:
                continue

            cancelled = [f for f in flights_today if f.status and "取消" in f.status]
            if len(cancelled) != len(flights_today):
                continue

            airport_label = "南竿" if airport == "LZN" else "北竿"
            message = f"{airport_label}今日班機全數取消，" + _ferry_suggestion(db, today)
            _upsert_advisory(db, today, "flight_cancel_wave", message)
        db.commit()
    finally:
        db.close()


def _ferry_suggestion(db, today: date) -> str:
    schedules = db.query(FerrySchedule).filter_by(date=today).all()
    if not schedules:
        return "船班資訊尚未同步，請直接查詢台馬之星官網。"

    normal = [s for s in schedules if s.status == "正常"]
    if normal:
        s = normal[0]
        return f"可考慮改搭今日 {s.sched_depart_time} 台馬之星（基隆→{s.route}，{s.arrive_order}）。"

    return "今日台馬之星也停航，請留意官方最新公告，暫無其他替代交通方式。"


def _upsert_advisory(db, d: date, type_: str, message: str) -> None:
    existing = db.query(Advisory).filter_by(date=d, type=type_).one_or_none()
    if existing:
        existing.message = message
    else:
        db.add(Advisory(date=d, type=type_, message=message))


def cleanup_old_data() -> None:
    """只保留最近 RETENTION_DAYS 天的航班資料。"""
    cutoff = date.today() - timedelta(days=RETENTION_DAYS)
    db = SessionLocal()
    try:
        db.query(Flight).filter(Flight.date < cutoff).delete()
        db.query(FerrySchedule).filter(FerrySchedule.date < cutoff).delete()
        db.query(Advisory).filter(Advisory.date < cutoff).delete()
        db.commit()
    finally:
        db.close()
