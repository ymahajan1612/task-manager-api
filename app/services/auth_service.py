
from app.database_models import User
from sqlalchemy import select

from app.exceptions import UserExistsError
from app.security import hash_password

def register_user(
    user_data,
    db
):
    # Check if user already exists
    stmt = select(User).where(User.email == user_data.email)
    existing_user = db.execute(stmt).scalar_one_or_none()

    if existing_user:
        raise UserExistsError("Email already registered")

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user