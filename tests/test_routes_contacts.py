import pytest


@pytest.mark.anyio
async def test_create_contact(client, contact_to_create, token):
    response = await client.post(
        "/api/contacts",
        json=contact_to_create,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == contact_to_create["first_name"]
    assert data["last_name"] == contact_to_create["last_name"]
    assert data["email"] == contact_to_create["email"]
    assert data["phone"] == contact_to_create["phone"]
    assert data["birthday"] == contact_to_create["birthday"]
    assert data["address"] == contact_to_create["address"]
    assert "id" in data


@pytest.mark.anyio
async def test_repeat_create_contact(client, contact_to_create, token):
    response = await client.post(
        "/api/contacts",
        json=contact_to_create,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "The contact's email and/or phone already exist"


@pytest.mark.anyio
async def test_read_contact(client, token, contact_to_create):
    response = await client.get(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == contact_to_create["first_name"]
    assert data["last_name"] == contact_to_create["last_name"]
    assert data["email"] == contact_to_create["email"]
    assert data["phone"] == contact_to_create["phone"]
    assert data["birthday"] == contact_to_create["birthday"]
    assert data["address"] == contact_to_create["address"]
    assert "id" in data


@pytest.mark.anyio
async def test_read_contact_not_found(client, token):
    response = await client.get(
        "/api/contacts/2", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.anyio
async def test_read_contacts(client, token, contact_to_create):
    response = await client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == contact_to_create["first_name"]
    assert data[0]["last_name"] == contact_to_create["last_name"]
    assert data[0]["email"] == contact_to_create["email"]
    assert data[0]["phone"] == contact_to_create["phone"]
    assert data[0]["birthday"] == contact_to_create["birthday"]
    assert data[0]["address"] == contact_to_create["address"]
    assert "id" in data[0]


@pytest.mark.anyio
async def test_read_contacts_search(
    client,
    token,
    contact_to_create,
    offset=0,
    limit=1000,
    first_name="test",
    last_name="test",
    email="test",
):
    response = await client.get(
        f"/api/contacts?offset={offset}&limit={limit}&first_name={first_name}&last_name={last_name}&email={email}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == contact_to_create["first_name"]
    assert data[0]["last_name"] == contact_to_create["last_name"]
    assert data[0]["email"] == contact_to_create["email"]
    assert data[0]["phone"] == contact_to_create["phone"]
    assert data[0]["birthday"] == contact_to_create["birthday"]
    assert data[0]["address"] == contact_to_create["address"]
    assert "id" in data[0]


@pytest.mark.anyio
async def test_read_contacts_birthdays_in_n_days(client, token, contact_to_create):
    response = await client.get(
        "/api/contacts/birthdays_in_1_days",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == contact_to_create["first_name"]
    assert data[0]["last_name"] == contact_to_create["last_name"]
    assert data[0]["email"] == contact_to_create["email"]
    assert data[0]["phone"] == contact_to_create["phone"]
    assert data[0]["birthday"] == contact_to_create["birthday"]
    assert data[0]["address"] == contact_to_create["address"]
    assert "id" in data[0]


@pytest.mark.anyio
async def test_read_contacts_birthdays_in_n_days_ext(
    client,
    token,
    contact_to_create,
    n=1,
    offset=0,
    limit=1000,
):
    response = await client.get(
        f"/api/contacts/birthdays_in_1_days?n={n}&offset={offset}&limit={limit}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == contact_to_create["first_name"]
    assert data[0]["last_name"] == contact_to_create["last_name"]
    assert data[0]["email"] == contact_to_create["email"]
    assert data[0]["phone"] == contact_to_create["phone"]
    assert data[0]["birthday"] == contact_to_create["birthday"]
    assert data[0]["address"] == contact_to_create["address"]
    assert "id" in data[0]


@pytest.mark.anyio
async def test_update_contact(client, token, contact_to_update):
    response = await client.put(
        "/api/contacts/1",
        json=contact_to_update,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == contact_to_update["first_name"]
    assert data["last_name"] == contact_to_update["last_name"]
    assert data["email"] == contact_to_update["email"]
    assert data["phone"] == contact_to_update["phone"]
    assert data["birthday"] == contact_to_update["birthday"]
    assert data["address"] == contact_to_update["address"]
    assert "id" in data


@pytest.mark.anyio
async def test_update_contact_not_found(client, token, contact_to_update):
    response = await client.put(
        "/api/contacts/2",
        json=contact_to_update,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


@pytest.mark.anyio
async def test_delete_contact(client, token):
    response = await client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 204, response.text


@pytest.mark.anyio
async def test_repeat_delete_contact(client, token):
    response = await client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"