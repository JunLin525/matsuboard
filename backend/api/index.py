"""Vercel Python serverless function 進入點，直接暴露 FastAPI 的 ASGI app。

⚠️ 還沒有實際部署驗證過：Vercel 的 Python runtime 需要能 import 到專案根目錄的
`common` package，屆時可能要在 vercel.json 用 `functions.includeFiles` 把
common/**、backend/** 一起打包，或是把這支檔案搬到 repo 根目錄視實際狀況調整。
"""

from backend.app.main import app  # noqa: F401
