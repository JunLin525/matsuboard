"""本機測試用 CLI，不需要 AWS，直接跑 pipeline 函式。

用法（在專案根目錄執行）：
    python -m scraper.local_run all
    python -m scraper.local_run flights
    python -m scraper.local_run ferries
    python -m scraper.local_run cleanup
"""

from __future__ import annotations

import sys

from common.db import init_db

from .pipeline import (
    cleanup_old_data,
    compute_advisory,
    refresh_ferry_announcements,
    refresh_flights,
    sync_ferry_schedule,
)


def run_all():
    refresh_flights()
    refresh_ferry_announcements()
    sync_ferry_schedule()
    compute_advisory()


TASKS = {
    "flights": refresh_flights,
    "ferries": refresh_ferry_announcements,
    "sync": sync_ferry_schedule,
    "advisory": compute_advisory,
    "cleanup": cleanup_old_data,
    "all": run_all,
}

if __name__ == "__main__":
    init_db()
    task_name = sys.argv[1] if len(sys.argv) > 1 else "all"
    task = TASKS.get(task_name)
    if task is None:
        print(f"未知任務: {task_name}，可用: {', '.join(TASKS)}")
        sys.exit(1)
    task()
    print(f"完成: {task_name}")
