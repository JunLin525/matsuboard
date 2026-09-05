"""AWS Lambda entrypoint：抓船班公告。EventBridge Scheduler 每 30-60 分鐘觸發一次。"""

from scraper.pipeline import refresh_ferry_announcements, sync_ferry_schedule


def handler(event=None, context=None):
    refresh_ferry_announcements()
    sync_ferry_schedule()
    return {"status": "ok"}
