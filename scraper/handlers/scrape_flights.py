"""AWS Lambda entrypoint：抓飛機動態。EventBridge Scheduler 每 5-10 分鐘觸發一次。"""

from scraper.pipeline import compute_advisory, refresh_flights, sync_ferry_schedule


def handler(event=None, context=None):
    refresh_flights()
    sync_ferry_schedule()
    compute_advisory()
    return {"status": "ok"}
