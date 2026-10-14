from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.database_models import User, Task
from app.config import DATABASE_URL, TEST_DATABASE_URL


test_engine = create_engine(TEST_DATABASE_URL)
engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_test_db():
    test_db = SessionLocalTest()
    try:
        yield test_db
    finally:
        test_db.close()


