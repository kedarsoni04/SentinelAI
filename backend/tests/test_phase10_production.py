import time
import uuid
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import create_access_token, decode_access_token, hash_password
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def test_user():
    session = SessionLocal()
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"prod_tester_{user_id[:8]}@sentinel.ai",
        name="Production Security Tester",
        password_hash=hash_password("SecurePassword123!"),
        role=UserRole.SECURITY_OPERATOR,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return user


def test_liveness_health_endpoint(client):
    """Verify GET /api/health returns 200 with service metadata and uptime."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentinelai-backend"
    assert data["version"] == "0.10.0"
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0


def test_readiness_endpoint(client):
    """Verify GET /api/ready verifies database connectivity and storage writability."""
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["ready"] is True
    assert data["checks"]["database"] == "reachable"
    assert data["checks"]["storage"] == "writable"


def test_request_id_tracing_header(client):
    """Verify X-Request-ID is generated and returned on all HTTP responses."""
    response = client.get("/api/health")
    assert "X-Request-ID" in response.headers
    req_id = response.headers["X-Request-ID"]
    assert len(req_id) > 10

    # Custom incoming X-Request-ID should be preserved
    custom_id = "test-custom-trace-id-12345"
    response2 = client.get("/api/health", headers={"X-Request-ID": custom_id})
    assert response2.headers["X-Request-ID"] == custom_id


def test_security_headers_enforced(client):
    """Verify HTTP security headers are attached to responses."""
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_jwt_token_lifecycle_and_expiration(test_user):
    """Verify JWT token signing, decoding, and expiration enforcement."""
    # 1. Valid token
    valid_token = create_access_token(test_user.id, expires_delta=timedelta(minutes=15))
    decoded_id = decode_access_token(valid_token)
    assert decoded_id == test_user.id

    # 2. Expired token
    expired_token = create_access_token(test_user.id, expires_delta=timedelta(seconds=-10))
    decoded_expired = decode_access_token(expired_token)
    assert decoded_expired is None

    # 3. Corrupted token
    corrupted_token = valid_token + "corrupted"
    decoded_corrupted = decode_access_token(corrupted_token)
    assert decoded_corrupted is None


def test_unauthenticated_protected_endpoint(client):
    """Verify protected endpoints return standardized 401 response with X-Request-ID."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "X-Request-ID" in response.headers
    data = response.json()
    assert "detail" in data
    assert "error" in data
    assert data["error"]["code"] == "HTTP_401"


def test_global_404_error_handling(client):
    """Verify non-existent endpoints return structured 404 response."""
    response = client.get("/api/non-existent-route-xyz")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    assert "request_id" in data["error"]


def test_rate_limiting_on_auth_login(client):
    """Verify in-memory rate limiter protects sensitive auth endpoints."""
    # Temporarily set a low limit and disable testing flag to test rate limiting
    orig_testing = settings.ENVIRONMENT
    orig_limit = settings.RATE_LIMIT_AUTH_PER_MINUTE
    try:
        settings.ENVIRONMENT = "production"
        settings.RATE_LIMIT_AUTH_PER_MINUTE = 3

        # First 3 requests allowed
        for _ in range(3):
            res = client.post("/api/auth/login", json={"email": "dummy@test.com", "password": "wrong"})
            assert res.status_code in (401, 404)

        # 4th request must be rate-limited with 429
        res4 = client.post("/api/auth/login", json={"email": "dummy@test.com", "password": "wrong"})
        assert res4.status_code == 429
        data = res4.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in res4.headers
    finally:
        settings.ENVIRONMENT = orig_testing
        settings.RATE_LIMIT_AUTH_PER_MINUTE = orig_limit
