# PRD：馬祖飛機停飛 × 船班備援看板（暫名 MatsuBoard）

## 1. 問題定義
馬祖（南竿/北竿）機場常因濃霧、強風導致班機取消，旅客常常到了松山機場才知道停飛，此時最需要的資訊是：**「今天/明天還有沒有船可以搭去馬祖？」**。目前這個資訊分散在民航局網站、立榮航空、馬祖海上交通訂位系統（matsuebs.com）等多個地方，沒有整合。

參考站：https://joeyang512.github.io/ferryboard/（小琉球版本的航班/船班動態整合看板）

## 2. 目標
一個單頁看板，同時顯示：
- 松山 ↔ 南竿/北竿 即時航班動態（正常/延誤/取消）
- 基隆 ↔ 馬祖（南竿線 + 東引線）台馬之星船班時刻與停航公告
- 當偵測到航班大量取消時，主動把「今晚/明天最近一班可搭的船」標示出來

## 3. 目標使用者
- 要從台北搭飛機去馬祖，擔心霧季取消的旅客/當地人
- 常駐馬祖、需要規劃返台/返鄉行程的居民

## 4. 核心功能（v1 MVP）

### 4.1 飛機動態
- 涵蓋南竿（LZN）+ 北竿（MFK）兩站，資料分開抓、分開顯示
- 顯示今日（可切換昨/今/明）松山—南竿、松山—北竿往返班次
- 欄位：航班編號、表定時間、預估/實際時間、狀態（準時/延誤/取消）、機型
- 取消班次特別標紅並統計「今日南竿共 X 班取消」「今日北竿共 X 班取消」

### 4.2 船班資訊
- 台馬之星「單馬雙東」全部呈現：南竿線 + 東引線都顯示，並標示當天航行順序（單號先馬後東 / 雙號先東後馬）
- 固定規則先寫死當基礎（每日 22:50 基隆開船，登船 21:30–22:30，週二停航保養），再用官網公告覆蓋「停航/加班」狀態
- 顯示：日期、開船時間、航行順序、狀態（正常/停航/公告連結）

### 4.3 整合提示（這個產品的核心價值）
- 規則：當某天航班取消比例超過閾值（例如全部取消，或使用者選的航班取消）→ 頁面頂部顯示提示卡「今日班機多數取消，可考慮搭乘 O月O日 22:50 台馬之星（基隆→南竿）」，並附船班連結
- 若當天船也停航（海象不佳），一併顯示警示，避免旅客兩頭空

### 4.4 資料更新
- 由 AWS EventBridge Scheduler 定時觸發 AWS Lambda（飛機每 5–10 分鐘、船班公告每 30–60 分鐘），Lambda 內用 httpx（+ BeautifulSoup 解析 HTML）實際打對方資料來源，寫入 Supabase（Postgres），Vercel 端 API 只負責讀取，前端輪詢拿最新資料
- 保留近期快照，方便做「取消率」統計（v2），但只保留**過去 3 天**的航班狀態資料，超過 3 天由每日排程的清理 Lambda 清掉（見 4.5 資料保存政策），資料庫大小可控

### 4.5 資料保存政策
- `flights` / `flight_snapshots`：只保留最近 3 天（含今天），每天一次由 EventBridge 觸發的清理 Lambda 刪除 `date < today - 3天` 的資料
- `ferry_schedules` / `advisories`：資料量小（一天頂多幾筆公告），先不特別清理，之後如果要做長期統計再視情況調整保留期

## 5. 非目標（v1 不做）
- 訂票/金流（導去官方連結即可）
- 帳號系統
- 多語言（先繁中）
- 通知的「發送」邏輯（Email/Telegram/LINE）— 留到 v2，但 v1 先把資料庫欄位留好（見 8.）

## 6. 資料來源（實測結果）

| 項目 | 來源 | 備註 |
|---|---|---|
| 即時航班 | 民航局「班機即時離到站資訊」`caa.gov.tw/ImmediateFlight.aspx` | 頁面是 AJAX 動態載入，需要打開瀏覽器 DevTools 找出實際的資料 API（沒有公開文件），實作時要 reverse-engineer |
| 船班/停航公告 | 馬祖海上交通訂位購票系統 `matsuebs.com`（首頁「最新消息」） | 同樣是前端動態渲染，公告文字型式不固定（如「9/5 新臺馬輪因海象不佳停航」），可能需要簡單規則/關鍵字解析，不保證 100% 結構化 |
| 備援/校對 | 馬祖航空站 `msa.gov.tw`、連江縣政府航班資訊頁 | 官方公告，人工可對照 |

⚠️ 風險：這兩個來源都沒有正式公開 API，屬於「非官方爬蟲」，需要：
1. 做好 User-Agent、頻率限制，避免造成對方網站負擔或被鎖 IP
2. 網站改版會讓爬蟲失效，需要設計成容易替換的 adapter 模式
3. 頁面上要放免責聲明「資料僅供參考，正確資訊請以官方為準」

## 7. 系統架構（全 serverless）
- **資料抓取層（AWS）**：AWS Lambda（Python）負責實際抓取，httpx（+ BeautifulSoup 解析 HTML）打對方資料來源；AWS EventBridge Scheduler 定時觸發（飛機 5–10 分鐘一次、船班公告 30–60 分鐘一次、清理任務每天一次）。不需要 Celery/Redis，Lambda + EventBridge 本身就是排程 + 執行的組合，pay-per-invocation，這個呼叫頻率幾乎落在免費額度內
- **資料庫**：**Supabase（Postgres）**取代本機 SQLite 檔案。原因：Lambda 和 Vercel function 都是無狀態、檔案系統不共用也不持久化，兩邊沒辦法共寫一個本機 SQLite 檔案，必須換成走網路連線的資料庫；Supabase 是主流的 Postgres BaaS，SQLAlchemy 原生支援、免費額度對這個規模夠用、有 Dashboard 方便除錯。⚠️ 注意：Lambda / Vercel function 都是「每次呼叫可能開新連線」的環境，兩邊都必須用 Supabase 的**連線池端點（Supavisor / PgBouncer，transaction mode）**，不能用一般直連字串，否則容易把連線數用光
- **API 層（Vercel）**：只保留簡單的讀取邏輯（`/api/flights`、`/api/ferries`、`/api/advisory`），單純查 Supabase 回傳 JSON，不做任何抓取/排程，符合 Vercel serverless function「短時間執行完」的限制
- **前端**：React（Vite）+ React Query（或 SWR）用 `refetchInterval` 做簡單輪詢（每 30–60 秒）；分頁背景時自動暫停輪詢。因為資料本身刷新頻率就是分鐘等級，輪詢已經足夠，不用 SSE
- **部署**：前端 + API 層都在 Vercel；抓取邏輯在 AWS（Lambda + EventBridge）；資料庫在 Supabase。三個平台都有免費額度，這個規模的專案理論上可以做到接近零成本

## 8. 資料模型草案（Supabase / Postgres）
- `flights(id, date, airport[LZN|MFK], flight_no, airline, origin, dest, sched_time, actual_time, status, fetched_at)`
- `flight_snapshots`（每次抓取的原始快照，方便除錯與統計）
- `ferry_schedules(id, date, route[南竿|東引], depart_port, arrive_order, sched_depart_time, status, note, source_url)`
- `advisories(id, date, type[flight_cancel_wave/ferry_cancel], message, created_at)`
- `subscriptions(id, channel[email|telegram|line], target, filter(JSON), is_active default false, created_at)` — v1 只建表不接 API，純占位給 v2 通知功能用

## 9. API 草案
- `GET /api/flights?date=YYYY-MM-DD&airport=LZN|MFK`
- `GET /api/ferries?date=YYYY-MM-DD&route=南竿|東引`
- `GET /api/advisory?date=YYYY-MM-DD` → 回傳「建議搭乘」卡片內容
- 不需要 `/internal/refresh`：抓取由 Lambda 排程直接寫入 Supabase，不經過 Vercel API

## 9.5 權限與存取控制（Supabase 免費方案）
- **DB 角色分權**：建兩個 Postgres role，不要兩邊都用預設的 `postgres` 超級使用者：
  - `scraper_writer`：只 GRANT `INSERT/UPDATE/DELETE` 給 Lambda 用（寫入 flights/ferry_schedules/advisories、跑清理任務）
  - `api_reader`：只 GRANT `SELECT` 給 Vercel API 用（讀取層帳密外洩頂多被看資料，不會被改/刪）
- **連線方式**：兩邊都走 Supabase 連線池端點（Supavisor，transaction mode），不要用直連字串，避免 serverless 每次呼叫開新連線把連線數用光
- **免費方案的網路限制**：Supabase 的 IP allowlist（Network Restrictions）通常是付費方案功能，免費方案預設連線池對外網開放，所以安全性主要靠「帳密夠強 + 角色權限夠小」，帳密只放在 Vercel/AWS 的環境變數（Secrets），不要進到前端或 git repo
- **CORS**：如果前端和 API 部署在同一個 Vercel 專案（同網域），不需要額外設定；如果分開部署，FastAPI 要設定 `CORSMiddleware` 允許前端網域

## 10. 待辦 / 下一步
1. 用瀏覽器 DevTools 探查 `caa.gov.tw/ImmediateFlight.aspx` 和 `matsuebs.com` 的實際資料 API/HTML 結構
2. 建立專案骨架（FastAPI + React monorepo 目錄）
3. 依探查結果實作 scraper adapter
4. 部署平台待議

## 11. 授權（License）

**選用**：PolyForm Noncommercial License 1.0.0（原始碼公開、允許自由使用/修改/散布，但限制僅供非商業用途；商業使用需另外向著作權人取得授權）。

> 備註：依 OSI（Open Source Initiative）的定義，限制商業使用的授權嚴格來說不算「開放原始碼（Open Source）」，業界通常稱這類授權為 **source-available**。實務上對外介紹時可以說「原始碼公開、非商用授權」，避免和 OSI 認證的 Open Source 授權混淆。

實作時把下面內容存成專案根目錄的 `LICENSE` 檔案，並把 `[Your Name / Org]` 換成你要掛名的著作權人（個人名字、GitHub 帳號或未來的組織名都可以）：

```text
# PolyForm Noncommercial License 1.0.0

<https://polyformproject.org/licenses/noncommercial/1.0.0>

Copyright (c) 2026 [Your Name / Org]

## Acceptance

In order to get any license under these terms, you must agree to them as both strict obligations and conditions to all your licenses.

## Copyright License

The licensor grants you a copyright license for the software to do everything you might do with the software that would otherwise infringe the licensor's copyright in it for any permitted purpose.  However, you may only distribute the software according to [Distribution License](#distribution-license) and make changes or new works based on the software according to [Changes and New Works License](#changes-and-new-works-license).

## Distribution License

The licensor grants you an additional copyright license to distribute copies of the software.  Your license to distribute covers distributing the software with changes and new works permitted by [Changes and New Works License](#changes-and-new-works-license).

## Notices

You must ensure that anyone who gets a copy of any part of the software from you also gets a copy of these terms or the URL for them above, as well as copies of any plain-text lines beginning with `Required Notice:` that the licensor provided with the software.  For example:

> Required Notice: Copyright Yoyodyne, Inc. (http://example.com)

## Changes and New Works License

The licensor grants you an additional copyright license to make changes and new works based on the software for any permitted purpose.

## Patent License

The licensor grants you a patent license for the software that covers patent claims the licensor can license, or becomes able to license, that you would infringe by using the software.

## Noncommercial Purposes

Any noncommercial purpose is a permitted purpose.

## Personal Uses

Personal use for research, experiment, and testing for the benefit of public knowledge, personal study, private entertainment, hobby projects, amateur pursuits, or religious observance, without any anticipated commercial application, is use for a permitted purpose.

## Noncommercial Organizations

Use by any charitable organization, educational institution, public research organization, public safety or health organization, environmental protection organization, or government institution is use for a permitted purpose regardless of the source of funding or obligations resulting from the funding.

## Fair Use

You may have "fair use" rights for the software under the law. These terms do not limit them.

## No Other Rights

These terms do not allow you to sublicense or transfer any of your licenses to anyone else, or prevent the licensor from granting licenses to anyone else.  These terms do not imply any other licenses.

## Patent Defense

If you make any written claim that the software infringes or contributes to infringement of any patent, your patent license for the software granted under these terms ends immediately. If your company makes such a claim, your patent license ends immediately for work on behalf of your company.

## Violations

The first time you are notified in writing that you have violated any of these terms, or done anything with the software not covered by your licenses, your licenses can nonetheless continue if you come into full compliance with these terms, and take practical steps to correct past violations, within 32 days of receiving notice.  Otherwise, all your licenses end immediately.

## No Liability

***As far as the law allows, the software comes as is, without any warranty or condition, and the licensor will not be liable to you for any damages arising out of these terms or the use or nature of the software, under any kind of legal claim.***

## Definitions

The **licensor** is the individual or entity offering these terms, and the **software** is the software the licensor makes available under these terms.

**You** refers to the individual or entity agreeing to these terms.

**Your company** is any legal entity, sole proprietorship, or other kind of organization that you work for, plus all organizations that have control over, are under the control of, or are under common control with that organization.  **Control** means ownership of substantially all the assets of an entity, or the power to direct its management and policies by vote, contract, or otherwise.  Control can be direct or indirect.

**Your licenses** are all the licenses granted to you for the software under these terms.

**Use** means anything you do with the software requiring one of your licenses.
```

另外建議在 `README.md` 補一行對應的 SPDX 識別（方便 GitHub 自動辨識授權）：
```
SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
```
