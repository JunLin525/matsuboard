"""Vercel Python serverless function 進入點，直接暴露 FastAPI 的 ASGI app。

這個專案在 Vercel 上要拆成兩個獨立專案：
- 前端專案：Root Directory 設成 `frontend`，Vercel 會用 Vite 零設定偵測，
  完全看不到這支檔案跟 repo 根目錄的 pyproject.toml。
- backend 專案：Root Directory 留在 repo 根目錄（預設值），這樣才 import
  得到跟 backend/ 同層的 `common` package；根目錄的 pyproject.toml
  用 [tool.vercel] entrypoint 指到這裡。
"""

from backend.app.main import app  # noqa: F401
