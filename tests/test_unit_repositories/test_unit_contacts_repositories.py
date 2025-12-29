import pytest
from unittest.mock import AsyncMock, Mock
from datetime import date, timedelta

from src.database.models import Contact, User, UserRole
from src.repositories.contacts import ContactRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def contact_repo(mock_session):
    return ContactRepository(session=mock_session)


@pytest.fixture
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="user@test.com",
        password="hashed_pass",
        role=UserRole.USER,
        is_verified=True
    )


@pytest.fixture
def mock_contact():
    return Contact(
        id=1,
        name="John",
        surname="Doe",
        email="john@example.com",
        phone="+1234567890",
        birthday=date(1990, 5, 15),
        info="Test contact",
        user_id=1
    )


async def test_create_contact(contact_repo, mock_session, mock_user):
    data = {
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "birthday": date(1990, 5, 15),
        "info": "Test contact"
    }

    contact = await contact_repo.create(data, mock_user)

    assert isinstance(contact, Contact)
    assert contact.name == "John"
    assert contact.surname == "Doe"
    assert contact.email == "john@example.com"
    assert contact.user == mock_user
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


async def test_get_all_contacts_without_query(contact_repo, mock_session, mock_user):
    contacts = [
        Contact(id=1, name="John", surname="Doe", email="john@example.com",
                phone="+111", birthday=date(1990, 1, 1), user_id=1),
        Contact(id=2, name="Jane", surname="Smith", email="jane@example.com",
                phone="+222", birthday=date(1992, 2, 2), user_id=1)
    ]

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repo.get_all(mock_user)

    assert len(result) == 2
    assert result[0].name == "John"
    assert result[1].name == "Jane"
    mock_session.execute.assert_awaited_once()


async def test_get_all_contacts_with_query(contact_repo, mock_session, mock_user):
    contacts = [
        Contact(id=1, name="John", surname="Doe", email="john@example.com",
                phone="+111", birthday=date(1990, 1, 1), user_id=1)
    ]

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repo.get_all(mock_user, query="John")

    assert len(result) == 1
    assert result[0].name == "John"
    mock_session.execute.assert_awaited_once()


async def test_get_contact_by_id(contact_repo, mock_session, mock_contact):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repo.get_by_id(1)

    assert result == mock_contact
    assert result.id == 1
    assert result.name == "John"
    mock_session.execute.assert_awaited_once()


async def test_get_contact_by_id_not_found(contact_repo, mock_session):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repo.get_by_id(999)

    assert result is None
    mock_session.execute.assert_awaited_once()


async def test_update_contact(contact_repo, mock_session, mock_contact):
    data = {
        "name": "Johnny",
        "phone": "+9876543210"
    }

    result = await contact_repo.update(mock_contact, data)

    assert result.name == "Johnny"
    assert result.phone == "+9876543210"
    assert result.surname == "Doe"  # Не изменилось
    mock_session.commit.assert_awaited_once()


async def test_delete_contact(contact_repo, mock_session, mock_contact):
    await contact_repo.delete(mock_contact)

    mock_session.delete.assert_awaited_once_with(mock_contact)
    mock_session.commit.assert_awaited_once()


async def test_upcoming_birthdays(contact_repo, mock_session):
    today = date.today()
    contacts = [
        Contact(id=1, name="John", surname="Doe", email="john@example.com",
                phone="+111", birthday=today + timedelta(days=3), user_id=1),
        Contact(id=2, name="Jane", surname="Smith", email="jane@example.com",
                phone="+222", birthday=today + timedelta(days=5), user_id=1)
    ]

    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = contacts
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repo.upcoming_birthdays()

    assert len(result) == 2
    assert result[0].birthday == today + timedelta(days=3)
    assert result[1].birthday == today + timedelta(days=5)
    mock_session.execute.assert_awaited_once()


async def test_upcoming_birthdays_empty(contact_repo, mock_session):
    mock_result = Mock()
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contact_repo.upcoming_birthdays()

    assert len(result) == 0
    mock_session.execute.assert_awaited_once()