from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.database_models import User, Task

TEST_DATABASE_URL = "postgresql+psycopg://postgres:xxx@localhost:5432/taskManager_test"

test_engine = create_engine(TEST_DATABASE_URL)

SessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def get_test_db():
    test_db = SessionLocalTest()
    try:
        yield test_db
    finally:
        test_db.close()


