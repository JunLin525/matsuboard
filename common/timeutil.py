from datetime import date, datetime
from zoneinfo import ZoneInfo

TAIPEI_TZ = ZoneInfo("Asia/Taipei")


def today_taipei() -> date:
    """全部「今天」都要用這個，不要用 date.today()——伺服器跑在 UTC，
    台灣時間每天 00:00-08:00 那段 date.today() 算出來的還是昨天。"""
    return datetime.now(TAIPEI_TZ).date()
