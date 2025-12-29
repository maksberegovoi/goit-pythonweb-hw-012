import pytest
from unittest.mock import AsyncMock
from src.database.models import User
from src.repositories.users import UserRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def user_repo(mock_session):
    return UserRepository(session=mock_session)


class UserCreateMock:
    password = "pass"
    def model_dump(self, **kwargs):
        return {"username": "test", "email": "a@b.com"}


async def test_create_user(user_repo, mock_session):
    data = UserCreateMock()
    avatar = "avatar_url"

    user = await user_repo.create_user(data, avatar)

    assert isinstance(user, User)
    assert user.username == "test"
    assert user.email == "a@b.com"
    assert user.password == "pass"
    assert user.avatar_url == avatar
    mock_session.add.assert_called_once_with(user)
    mock_session.commit.assert_awaited()
    mock_session.refresh.assert_awaited()


async def test_get_user_by_email(user_repo, mock_session):
    user = User(id=1, username="test", email="a@b.com", password="pass")

    from unittest.mock import Mock
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = user

    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_email("a@b.com")
    assert result == user
    mock_session.execute.assert_awaited()


async def test_get_user_by_username(user_repo, mock_session):
    user = User(id=1, username="test", email="a@b.com", password="pass")

    from unittest.mock import Mock
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_username("test")
    assert result == user
    mock_session.execute.assert_awaited()


async def test_set_user_verified(user_repo, mock_session):
    user = User(id=1, username="test", email="a@b.com", password="pass", is_verified=False)
    user_repo.get_user_by_email = AsyncMock(return_value=user)

    await user_repo.set_user_verified("a@b.com")
    assert user.is_verified is True
    mock_session.commit.assert_awaited()


async def test_update_avatar_url(user_repo, mock_session):
    user = User(id=1, username="test", email="a@b.com", password="pass", avatar_url=None)
    user_repo.get_user_by_email = AsyncMock(return_value=user)

    result = await user_repo.update_avatar_url("a@b.com", "new_avatar.png")
    assert user.avatar_url == "new_avatar.png"
    assert result == user
    mock_session.commit.assert_awaited()
    mock_session.refresh.assert_awaited()


async def test_set_new_password(user_repo, mock_session):
    user = User(id=1, username="test", email="a@b.com", password="old_pass")
    user_repo.get_user_by_email = AsyncMock(return_value=user)

    await user_repo.set_new_password("new_pass", "a@b.com")
    assert user.password == "new_pass"
    mock_session.commit.assert_awaited()


async def test_set_temp_password(user_repo, mock_session):
    user = User(id=1, username="test", email="a@b.com", password="pass", temp_password=None)
    user_repo.get_user_by_email = AsyncMock(return_value=user)

    await user_repo.set_temp_password("temp_pass", "a@b.com")
    assert user.temp_password == "temp_pass"
    mock_session.commit.assert_awaited()
