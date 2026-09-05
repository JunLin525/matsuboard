from __future__ import annotations

import os
from datetime import date, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from common.db import SessionLocal
from common.models import Advisory, FerrySchedule, Flight
from common.timeutil import today_taipei

app = FastAPI(title="MatsuBoard API")

# 前端跟 API 若分開部署，把 FRONTEND_ORIGIN 設成實際網域；同網域部署則不需要 CORS。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "*")],
    allow_methods=["GET"],
    allow_headers=["*"],
)

AIRPORT_LABEL = {"LZN": "南竿", "MFK": "北竿"}
DIRECTION_LABEL = {"D": "離站", "A": "到站"}


def _parse_date(value: str | None) -> date:
    return date.fromisoformat(value) if value else today_taipei()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/flights")
def get_flights(date: str | None = Query(None), airport: str | None = Query(None)):
    target_date = _parse_date(date)
    db = SessionLocal()
    try:
        query = db.query(Flight).filter(Flight.date == target_date)
        if airport:
            query = query.filter(Flight.airport == airport)
        rows = query.order_by(Flight.airport, Flight.direction, Flight.sched_time).all()
        return {
            "date": target_date.isoformat(),
            "flights": [
                {
                    "airport": f.airport,
                    "airport_label": AIRPORT_LABEL.get(f.airport, f.airport),
                    "direction": f.direction,
                    "direction_label": DIRECTION_LABEL.get(f.direction, f.direction),
                    "flight_no": f.flight_no,
                    "airline": f.airline,
                    "other_airport": f.other_airport,
                    "sched_time": f.sched_time,
                    "actual_time": f.actual_time,
                    "aircraft_type": f.aircraft_type,
                    "terminal": f.terminal,
                    "status": f.status,
                    "fetched_at": f.fetched_at.isoformat() if f.fetched_at else None,
                }
                for f in rows
            ],
        }
    finally:
        db.close()


@app.get("/api/ferries")
def get_ferries(date: str | None = Query(None), route: str | None = Query(None)):
    target_date = _parse_date(date)
    db = SessionLocal()
    try:
        query = db.query(FerrySchedule).filter(FerrySchedule.date == target_date)
        if route:
            query = query.filter(FerrySchedule.route == route)
        rows = query.order_by(FerrySchedule.route).all()
        return {
            "date": target_date.isoformat(),
            "ferries": [
                {
                    "route": r.route,
                    "depart_port": r.depart_port,
                    "arrive_order": r.arrive_order,
                    "sched_depart_time": r.sched_depart_time,
                    "status": r.status,
                    "note": r.note,
                    "source_url": r.source_url,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


@app.get("/api/advisory")
def get_advisory(date: str | None = Query(None)):
    target_date = _parse_date(date)
    db = SessionLocal()
    try:
        rows = db.query(Advisory).filter(Advisory.date == target_date).all()
        return {
            "date": target_date.isoformat(),
            "advisories": [{"type": a.type, "message": a.message} for a in rows],
        }
    finally:
        db.close()


def _status_bucket(status: str | None) -> str:
    if not status:
        return "other"
    if "取消" in status:
        return "critical"
    if "延誤" in status:
        return "warning"
    if any(k in status for k in ("準時", "已飛", "已到")):
        return "good"
    return "other"


@app.get("/api/stats")
def get_stats(days: int = Query(3, ge=1, le=14)):
    """近 N 天(含今天)每個機場的航班狀態分佈，給前端畫堆疊長條圖用。

    只有 3 天保留期內的資料撐得住這個查詢；超過保留期的日子會回傳全 0。
    """
    end = today_taipei()
    start = end - timedelta(days=days - 1)
    db = SessionLocal()
    try:
        rows = db.query(Flight).filter(Flight.date >= start, Flight.date <= end).all()

        counts: dict[tuple[str, str], dict[str, int]] = {}
        for f in rows:
            key = (f.date.isoformat(), f.airport)
            bucket = counts.setdefault(key, {"good": 0, "warning": 0, "critical": 0, "other": 0})
            bucket[_status_bucket(f.status)] += 1

        stats = []
        current = start
        while current <= end:
            for airport in ("LZN", "MFK"):
                bucket = counts.get(
                    (current.isoformat(), airport),
                    {"good": 0, "warning": 0, "critical": 0, "other": 0},
                )
                stats.append(
                    {
                        "date": current.isoformat(),
                        "airport": airport,
                        "airport_label": AIRPORT_LABEL.get(airport, airport),
                        "total": sum(bucket.values()),
                        **bucket,
                    }
                )
            current += timedelta(days=1)

        return {"start": start.isoformat(), "end": end.isoformat(), "stats": stats}
    finally:
        db.close()
