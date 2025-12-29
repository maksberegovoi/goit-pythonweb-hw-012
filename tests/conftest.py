import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from main import app
from src.database.models import Base
from src.database.db import get_db
from src.conf.config import config
from src.services.auth import create_access_token
from src.database.models import User
from src.database.models import UserRole
from sqlalchemy.engine.url import make_url

original_url = make_url(config.DB_URL)
TEST_DATABASE_URL = original_url.set(database="test_db")
SYSTEM_DATABASE_URL = original_url.set(database="postgres")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    engine_system = create_async_engine(
        SYSTEM_DATABASE_URL,
        echo=False,
        isolation_level="AUTOCOMMIT"
    )
    async with engine_system.connect() as conn:
        try:
            await conn.execute(text("DROP DATABASE IF EXISTS test_db WITH (FORCE)"))
        except Exception:
            pass

        try:
            await conn.execute(text("CREATE DATABASE test_db"))
        except Exception as e:
            # проверяем код ошибки уникальности
            if "already exists" not in str(e):
                raise

    yield

    async with engine_system.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS test_db WITH (FORCE)"))
    await engine_system.dispose()


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False,
                                  poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(bind=test_engine,
                                         expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def override_get_db(db_session):
    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(override_get_db):
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = None
    mocker.patch("src.services.auth.redis_db", mock)
    return mock


@pytest.fixture(scope="module", autouse=True)
def disable_rate_limiter():
    from src.core.limiter import limiter
    original_value = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = original_value


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(
        username="test",
        email="test@example.com",
        password="test",
        role=UserRole.USER,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def token(test_user):
    return await create_access_token(data={"sub": test_user.username})


@pytest_asyncio.fixture
async def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client

