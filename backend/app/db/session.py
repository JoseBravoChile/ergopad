from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import os

# engine = create_engine('postgresql://hello:world@postgres:5432/hello')
engine = create_engine(f'postgresql://ergopad:8e!8Ba8!64xCk3i@postgres:5432/ergopad')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
