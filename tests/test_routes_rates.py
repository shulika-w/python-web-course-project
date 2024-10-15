from unittest.mock import MagicMock, AsyncMock
import pytest

image_id = 1
body_test = {
    "rate": 4
}

rate_id = 1
user_id = 1


@pytest.mark.anyio
async def test_read_all_my_rates(client, token):
    response = await client.get(
        f"/api/rates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


@pytest.mark.anyio
async def test_read_all_avg_rates(client, token):
    response = await client.get(
        f"/api/rates/avg_all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


###from routes/images.py####
@pytest.mark.anyio
async def test_read_all_rates_to_image(client, token):
    response = await client.get(
        f"/api/images/{image_id}/rates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


####from routes/images.py####
@pytest.mark.anyio
async def test_read_avg_rate_to_image(client, token):
    response = await client.get(
        f"/api/images/{image_id}/avg",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404, response.text


###from routes/users.py####
@pytest.mark.anyio
async def test_read_all_user_rates(client, token):
    response = await client.get(
        f"/api/users/{user_id}/rates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


###from routes/images.py####
@pytest.mark.anyio
async def test_create_rate_to_image(client, token):
    response = await client.post(
        f"/api/images/{image_id}/rates",
        json=body_test,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404, response.text


@pytest.mark.anyio
async def test_delete_rate_to_image(client, token):
    rate_id = 1
    response = await client.delete(
        f"/api/rates/{rate_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, response.text
