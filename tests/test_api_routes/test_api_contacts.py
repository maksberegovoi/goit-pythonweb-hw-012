import pytest


@pytest.mark.asyncio
async def test_create_contact(authorized_client):
    response = await authorized_client.post(
        "/contacts/",
        json={
            "name": "John",
            "surname": "Doe",
            "email": "john.doe@example.com",
            "phone": "123456789",
            "birthday": "1990-01-01",
            "info":"Best friend"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_contacts(authorized_client):
    await authorized_client.post(
        "/contacts/",
        json={
            "name": "Test", "surname": "Test",
            "email": "t@t.com", "phone": "111",
            "birthday": "2000-01-01", "info": ""
        }
    )

    response = await authorized_client.get("/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_contact_by_id(authorized_client):
    create_res = await authorized_client.post(
        "/contacts/",
        json={
            "name": "FindMe", "surname": "Test",
            "email": "find@me.com", "phone": "222",
            "birthday": "2000-01-01", "info": ""
        }
    )
    contact_id = create_res.json()["id"]

    response = await authorized_client.get(f"/contacts/{contact_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "FindMe"


@pytest.mark.asyncio
async def test_get_contact_not_found(authorized_client):
    response = await authorized_client.get("contacts/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_contact(authorized_client):
    create_res = await authorized_client.post(
        "/contacts/",
        json={
            "name": "DeleteMe", "surname": "Test",
            "email": "del@me.com", "phone": "444",
            "birthday": "2000-01-01", "info": ""
        }
    )
    contact_id = create_res.json()["id"]

    response = await authorized_client.delete(f"/contacts/{contact_id}")
    assert response.status_code == 200

    get_res = await authorized_client.get(f"/contacts/{contact_id}")
    assert get_res.status_code == 404
