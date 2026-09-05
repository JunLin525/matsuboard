"""Vercel Python serverless function 進入點，直接暴露 FastAPI 的 ASGI app。

這個專案在 Vercel 上要拆成兩個獨立專案：
- 前端專案：Root Directory 設成 `frontend`，Vercel 會用 Vite 零設定偵測，
  完全看不到這支檔案跟 repo 根目錄的 pyproject.toml。
- backend 專案：Root Directory 留在 repo 根目錄（預設值）。

實測發現 Vercel 打包這個 function 時，只會把 `backend/` 底下的東西包進去，
不會連同層的 `common/` 一起打包（跑出來是 ModuleNotFoundError: No module
named 'common'）。所以 `backend/common/` 是刻意複製一份 `common/` 進來，
只給這個 Vercel function 用；本機開發跟 scraper 還是吃 repo 根目錄那份
`common/`（sys.path 上repo 根目錄在前面，優先解析到那份）。如果改了
`common/models.py` 的 schema，記得同步複製一份到 `backend/common/`。
"""

from backend.app.main import app  # noqa: F401
