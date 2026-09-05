# MatsuBoard

SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

馬祖飛機停飛 × 船班備援看板。詳細規劃見 [PRD.md](./PRD.md)。

## 專案結構

```
common/     共用的 SQLAlchemy models + DB session（backend 和 scraper 都會 import）
backend/    FastAPI 讀取 API（本機用 uvicorn 跑，之後部署到 Vercel）
scraper/    抓取邏輯（本機用 local_run.py 跑，之後部署到 AWS Lambda + EventBridge）
frontend/   React (Vite) 前端
```

## 本機開發

預設用本機 SQLite 檔案（`matsuboard.db`），不需要先申請 Supabase 帳號就能跑起來。

### 1. 安裝 Python 依賴

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r scraper/requirements.txt
```

### 2. 跑一次抓取，把資料填進資料庫

在專案根目錄執行（注意是用 `-m`，這樣 `common`/`scraper` 才能被正確 import）：

```bash
python -m scraper.local_run all
```

這會依序：抓南竿/北竿即時航班、抓 matsuebs.com 最新公告、產生台馬之星固定船班骨架、算出建議提示卡。

其他可用的子命令：`flights` / `ferries` / `sync` / `advisory` / `cleanup`。

### 3. 啟動後端 API

```bash
uvicorn backend.app.main:app --reload --port 8000
```

打開 http://localhost:8000/api/flights 應該能看到今天的航班 JSON。

### 4. 啟動前端

```bash
cd frontend
npm install
cp .env.example .env.local   # 預設指向 http://localhost:8000
npm run dev
```

打開 Vite 印出的網址（預設 http://localhost:5173）。

### 5. 讓資料保持更新

本機開發沒有排程器，要手動或用 cron 定期重跑 `python -m scraper.local_run all`（例如用 `watch -n 300` 每 5 分鐘跑一次）才看得到新資料。正式環境這件事交給 AWS EventBridge Scheduler。

## 部署（規劃中，尚未實際跑過）

- **前端 + 讀取 API**：Vercel（`backend/api/index.py` 暴露 FastAPI app；`common` package 需要一起打包，實際部署時再依 Vercel Python runtime 的規則調整 `vercel.json`）
- **抓取邏輯**：AWS Lambda（`scraper/handlers/*.py` 的 `handler` 函式），用 EventBridge Scheduler 排程觸發
- **資料庫**：Supabase（Postgres），把 `DATABASE_URL` 換成 Supabase 連線池（Supavisor，transaction mode）字串即可，程式碼不用改
- **權限**：DB 建議分兩個角色——`scraper_writer`（給 Lambda，只給 INSERT/UPDATE/DELETE）、`api_reader`（給 Vercel，只給 SELECT），細節見 PRD 9.5 節

## 已知限制

- CAA 和 matsuebs.com 都不是官方公開 API，是爬蟲，網站改版可能讓 adapter 失效（見 `scraper/adapters/`）
- 船班公告的日期/類型是用關鍵字從標題猜的（`extract_dates_from_title` / `_classify`），不保證 100%準確
- 授權採用 [PolyForm Noncommercial License 1.0.0](./LICENSE)，記得把 LICENSE 檔案裡的 `[Your Name / Org]` 換成實際著作權人
