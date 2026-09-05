"""AWS Lambda entrypoint：每日清理超過保留期的資料。EventBridge Scheduler 每天觸發一次。"""

from scraper.pipeline import cleanup_old_data


def handler(event=None, context=None):
    cleanup_old_data()
    return {"status": "ok"}
