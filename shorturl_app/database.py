from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# База данных в файле data/url.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/url.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
