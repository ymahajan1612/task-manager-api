from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.database_models import User, Task
from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



