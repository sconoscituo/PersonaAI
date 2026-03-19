import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """테스트용 비동기 HTTP 클라이언트"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    """루트 엔드포인트 응답 확인"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PersonaAI"
    assert data["status"] == "running"
    assert "notice" in data  # 개인정보 보호 안내 포함 확인


@pytest.mark.asyncio
async def test_health(client):
    """헬스 체크 확인"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_and_login(client):
    """회원가입 및 로그인 흐름 확인"""
    # 회원가입
    reg_resp = await client.post(
        "/users/register",
        json={"email": "persona@example.com", "password": "password123"},
    )
    assert reg_resp.status_code == 201
    user = reg_resp.json()
    assert user["email"] == "persona@example.com"
    assert user["is_premium"] is False
    assert user["analysis_count"] == 0

    # 로그인
    login_resp = await client.post(
        "/users/login",
        json={"email": "persona@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_duplicate_email(client):
    """이메일 중복 가입 거부 확인"""
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/users/register", json=payload)
    resp = await client.post("/users/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_analyze_unauthorized(client):
    """인증 없이 분석 요청 시 거부 확인"""
    resp = await client.post("/analyze", json={"input_url": "https://instagram.com/test"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_platform_detection():
    """플랫폼 감지 로직 단위 테스트"""
    from app.services.scraper import detect_platform

    platform, username = detect_platform("https://www.instagram.com/cristiano/")
    assert platform == "instagram"
    assert username == "cristiano"

    platform, username = detect_platform("https://twitter.com/elonmusk")
    assert platform == "twitter"
    assert username == "elonmusk"

    platform, username = detect_platform("@testuser")
    assert platform == "instagram"
    assert username == "testuser"
