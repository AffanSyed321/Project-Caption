from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.caption import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./captions.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
