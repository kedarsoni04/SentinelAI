from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.schemas.user import MessageResponse, TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import authenticate_user, get_user_by_id, register_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# HTTP Bearer scheme for protected endpoints
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Dependency: extracts and validates the Bearer JWT token,
    returning the authenticated UserResponse.

    Raises:
        401 UNAUTHORIZED — if the token is missing, invalid, or expired.
    """
    token = credentials.credentials
    user_id = decode_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse.model_validate(user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(data: UserRegister, db: Session = Depends(get_db)) -> UserResponse:
    """
    Register a new SentinelAI user account.

    - Validates input and email format (via Pydantic).
    - Prevents duplicate email registration.
    - Securely hashes the password with bcrypt.
    - Returns the created user (without password hash).
    """
    return register_user(db, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT token",
)
def login(data: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate with email and password.

    Returns a JWT access token and the authenticated user object.
    """
    return authenticate_user(db, data.email, data.password)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Returns the profile of the currently authenticated user.
    Requires a valid Bearer JWT token.
    """
    return current_user
