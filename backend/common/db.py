import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()  # 讀專案根目錄的 .env（沒有就跳過），本機開發用來放 Supabase 連線字串

# 本機開發預設用 SQLite 檔案；正式環境把 DATABASE_URL 指到 Supabase 的
# connection pooler (Supavisor, transaction mode) 連線字串即可，其餘程式碼不用改。
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./matsuboard.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    """建立所有資料表（本機開發/初次啟動用；Supabase 上線後建議改用 migration 工具管理）。"""
    from . import models  # noqa: F401  (確保 model 都被註冊到 Base.metadata)

    Base.metadata.create_all(bind=engine)
