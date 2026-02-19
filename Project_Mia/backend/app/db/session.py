"""数据库连接配置"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 数据库文件路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

STATIC_DB_PATH = DATA_DIR / "static_content.db"
PROFILE_DB_PATH = DATA_DIR / "femo_profile.db"

# SQLAlchemy引擎
static_engine = create_engine(f"sqlite:///{STATIC_DB_PATH}", echo=False)
profile_engine = create_engine(f"sqlite:///{PROFILE_DB_PATH}", echo=False)

# Session工厂
StaticSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=static_engine)
ProfileSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=profile_engine)

# 依赖注入
def get_static_db():
    db = StaticSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_profile_db():
    db = ProfileSessionLocal()
    try:
        yield db
    finally:
        db.close()
