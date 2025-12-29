import pytest
from src.database.models import User
from sqlalchemy import select


@pytest.mark.asyncio
async def test_register_user(client, db_session):
    response = await client.post(
        "/api/auth/registration",
        json={
            "username": "test",
            "email": "test@example.com",
            "password": "test",
            "role": "user"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test"
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"
    assert "id" in data

    stmt = select(User).where(User.username == "test")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None


@pytest.mark.asyncio
async def test_register_existing_email(client, test_user):
    response = await client.post(
        "/api/auth/registration",
        json={
            "username": "another",
            "email": test_user.email,
            "password": "password123",
            "role": "user"
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_user(client, db_session):
    await client.post(
        "/api/auth/registration",
        json={"username": "loginuser", "email": "l@ex.com",
              "password": "mypassword","role": "user"}
    )

    stmt = select(User).where(User.username == "loginuser")
    res = await db_session.execute(stmt)
    user: User = res.scalar_one()
    user.is_verified = True
    await db_session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": "loginuser", "password": "mypassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"