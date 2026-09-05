"""
馬祖海上交通訂位購票系統（matsuebs.com）首頁「最新消息」爬蟲。

跟 CAA 不同，這裡是單純 server-rendered 的靜態 HTML table，不需要處理
postback/session，GET 首頁直接解析即可。

公告標題沒有結構化欄位（例如「9/5 新臺馬輪因海象不佳(5基出、6馬回)停航」），
只能用關鍵字粗略判斷公告類型，這是 PRD 裡已知的限制，不保證 100% 準確。
"""

from __future__ import annotations

import re
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

MATSUEBS_URL = "https://www.matsuebs.com/"

USER_AGENT = "MatsuBoard-Scraper/1.0 (personal non-commercial project; ferry status lookup)"

CANCEL_KEYWORDS = ["停航"]
EXTRA_KEYWORDS = ["加開", "加班"]
CHANGE_KEYWORDS = ["異動", "改航", "改期"]


def fetch_ferry_announcements() -> list[dict]:
    with httpx.Client(timeout=20, headers={"User-Agent": USER_AGENT}) as client:
        resp = client.get(MATSUEBS_URL)
        resp.raise_for_status()
        return _parse_news(resp.text)


def _parse_news(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []

    for link in soup.select("a[href^='/news/Detail/']"):
        tr = link.find_parent("tr")
        if tr is None:
            continue

        news_id = link["href"].rsplit("/", 1)[-1]
        title = link.get_text(strip=True)

        badge = tr.select_one("span.badge")
        category = badge.get_text(strip=True) if badge else None

        published = None
        for td in tr.find_all("td"):
            text = td.get_text(strip=True)
            m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", text)
            if m:
                published = datetime.strptime(text, "%Y/%m/%d").date()
                break

        rows.append(
            {
                "news_id": news_id,
                "title": title,
                "category": category,
                "published_date": published,
                "pinned": "置頂" in tr.get_text(),
                "url": f"https://www.matsuebs.com/news/Detail/{news_id}",
                "parsed_status": _classify(title),
            }
        )
    return rows


def _classify(title: str) -> str:
    if any(k in title for k in CANCEL_KEYWORDS):
        return "cancelled"
    if any(k in title for k in EXTRA_KEYWORDS):
        return "extra"
    if any(k in title for k in CHANGE_KEYWORDS):
        return "changed"
    return "unknown"


def extract_dates_from_title(title: str, year: int) -> list[date]:
    """從公告標題抓出「9/5」「9/6-9/7」這類日期片段，回傳當年度對應日期。"""
    dates = []
    for m in re.finditer(r"(\d{1,2})/(\d{1,2})", title):
        month, day = int(m.group(1)), int(m.group(2))
        try:
            dates.append(date(year, month, day))
        except ValueError:
            continue
    return dates


def ferry_route_order(d: date) -> str:
    """台馬之星「單馬雙東」規則：單號日期先到南竿，雙號日期先到東引。"""
    return "先馬後東" if d.day % 2 == 1 else "先東後馬"
