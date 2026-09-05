"""
交通部民用航空局「班機即時離到站資訊」爬蟲。

網頁是標準 ASP.NET WebForms postback（非 JSON API）：
1. GET 頁面，取出 __VIEWSTATE / __VIEWSTATEGENERATOR / __EVENTVALIDATION
2. 帶著這些隱藏欄位 + 機場/航線/離到站選項 POST 回同一個網址
3. 回傳的整頁 HTML 裡有一個 table.footable.timetable，逐列解析

實測結果（2026-09-05）：
- 機場代碼：南竿=LZN，北竿=MFK（下拉選單 name="ctl00$ContentPlaceHolder1$ddlAirport"）
- 航線固定選「國內」= rdolSelectLine=1
- 離站/到站：rdolSelectAorD = "D" / "A"
"""

from __future__ import annotations

import re
import ssl

import httpx
from bs4 import BeautifulSoup

CAA_URL = "https://www.caa.gov.tw/ImmediateFlight.aspx?a=270&lang=1"

USER_AGENT = "MatsuBoard-Scraper/1.0 (personal non-commercial project; flight status lookup)"


def _build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    # Python 3.13 起預設會檢查 VERIFY_X509_STRICT，caa.gov.tw 的憑證缺少
    # Subject Key Identifier 這個 extension，嚴格模式下會驗證失敗，這裡放寬。
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


def _client() -> httpx.Client:
    return httpx.Client(
        verify=_build_ssl_context(),
        timeout=20,
        headers={"User-Agent": USER_AGENT},
    )


def fetch_caa_flights(airport: str, direction: str) -> list[dict]:
    """抓取指定機場/方向的即時航班列表。

    airport: "LZN"（南竿）或 "MFK"（北竿）
    direction: "D"（離站）或 "A"（到站）

    GET 跟 POST 刻意用兩個獨立的 client（不共用 cookie jar）：caa.gov.tw 會
    回傳含中文的 Set-Cookie，httpx 的 cookiejar 在把它塞回下一次請求的
    Cookie header 時，內部編碼會誤判成 ascii 而丟出 UnicodeEncodeError。
    這個 postback 流程只需要 __VIEWSTATE 等隱藏欄位，不需要靠 cookie 維持
    session，所以乾脆不共用 client，直接避開這個問題。
    """
    with _client() as client:
        resp = client.get(CAA_URL)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    def hidden(field_id: str) -> str:
        tag = soup.find("input", {"id": field_id})
        return tag["value"] if tag and tag.has_attr("value") else ""

    data = {
        "__VIEWSTATE": hidden("__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": hidden("__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": hidden("__EVENTVALIDATION"),
        "ctl00$ContentPlaceHolder1$ddlAirport": airport,
        "ctl00$ContentPlaceHolder1$rdolSelectLine": "1",
        "ctl00$ContentPlaceHolder1$rdolSelectAorD": direction,
        "ctl00$ContentPlaceHolder1$btnSearch": "查詢",
    }
    with _client() as client:
        resp2 = client.post(CAA_URL, data=data, headers={"Referer": CAA_URL})
        resp2.raise_for_status()
        return _parse_flight_table(resp2.text)


def _parse_flight_table(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.footable.timetable")
    if table is None:
        return []

    rows: list[dict] = []
    for tr in table.select("tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 7:
            continue

        airline_flight = cells[2].get_text(" ", strip=True)
        parts = [p.strip() for p in re.split(r"/", airline_flight) if p.strip()]
        airline = parts[0] if parts else ""
        flight_no = parts[1] if len(parts) > 1 else ""

        aircraft_span = cells[4].find("span")
        aircraft_type = aircraft_span.get_text(strip=True) if aircraft_span else cells[4].get_text(strip=True)

        rows.append(
            {
                "sched_time": cells[0].get_text(strip=True),
                "actual_time": cells[1].get_text(strip=True),
                "airline": airline,
                "flight_no": flight_no,
                "other_airport": cells[3].get_text(strip=True),
                "aircraft_type": aircraft_type,
                "terminal": cells[5].get_text(strip=True),
                "status": cells[6].get_text(strip=True),
            }
        )
    return rows
