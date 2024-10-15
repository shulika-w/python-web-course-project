from unittest.mock import MagicMock, AsyncMock

import pytest

from app.src.services._cloudinary import cloudinary_service


@pytest.mark.anyio
async def test_read_or_create_tag(client, token):
    tag_title = "test"
    response = await client.get(
        f"/api/tags/{tag_title}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == tag_title


@pytest.mark.anyio
async def test_read_tags(client, token):
    tag_title = "test"
    response = await client.get(
        f"/api/tags",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["title"] == tag_title


@pytest.mark.anyio
async def test_delete_tag(client, token):
    tag_title = "test"
    response = await client.delete(
        f"/api/tags/{tag_title}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204, response.text
