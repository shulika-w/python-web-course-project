from unittest.mock import MagicMock, AsyncMock

import pytest

from app.src.services._cloudinary import cloudinary_service


@pytest.mark.anyio
async def test_read_me(client, user, token):
    response = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == user.get("email")


@pytest.mark.anyio
async def test_update_me(client, user_to_update, token):
    response = await client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        data=user_to_update,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == user_to_update.get("first_name")
    assert data["last_name"] == user_to_update.get("last_name")
    assert data["phone"] == user_to_update.get("phone")
    assert data["birthday"] == user_to_update.get("birthday")
