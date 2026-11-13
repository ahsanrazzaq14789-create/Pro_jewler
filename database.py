import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
URL=os.getenv("DATABASE_URL","sqlite:///./goldsilver_dev.db")
kwargs={"check_same_thread":False} if URL.startswith("sqlite") else {}
engine=create_engine(URL,connect_args=kwargs,pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
