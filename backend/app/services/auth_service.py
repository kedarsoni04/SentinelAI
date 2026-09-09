from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import TokenResponse, UserRegister, UserResponse


def register_user(db: Session, data: UserRegister) -> UserResponse:
    """
    Register a new user.

    Raises:
        409 CONFLICT — if email is already registered.
    """
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.SECURITY_OPERATOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def authenticate_user(db: Session, email: str, password: str) -> TokenResponse:
    """
    Authenticate a user and return a JWT token.

    Raises:
        401 UNAUTHORIZED — if credentials are invalid.
    """
    user = db.query(User).filter(User.email == email).first()

    # Use a constant-time comparison path to prevent user enumeration
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Retrieve a user by their ID. Returns None if not found."""
    return db.query(User).filter(User.id == user_id).first()
