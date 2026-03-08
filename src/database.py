import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Grab the URL from the environment, defaulting to a local SQLite file in a 'data' folder
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/finance.db")

# SQLite needs this specific flag to play nicely with FastAPI's async thread pooling
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
