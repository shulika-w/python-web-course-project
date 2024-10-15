from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
import pytest

from app.src.services._cloudinary import cloudinary_service
from app.src.schemas.comments import CommentModel

body_test = CommentModel(
    text="string11"
)
comment_id = 1
image_id = 1
body_test = {
    "text": "test_comment"
}
body = body_test
user_id = 1


@pytest.mark.anyio
async def test_read_all_my_comments(client, token):
    response = await client.get(
        f"/api/comments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


@pytest.mark.anyio
async def test_read_all_comments_to_comment(client, token):
    response = await client.get(
        f"/api/comments/{comment_id}/subcomments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


@pytest.mark.anyio
async def test_create_comment_to_comment(client, token):
    response = await client.post(
        f"/api/comments/{comment_id}/subcomments",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404, response.text


###from routes/images.py####
@pytest.mark.anyio
async def test_read_all_comments_to_image(client, token):
    response = await client.get(
        f"/api/images/{image_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


###from routes/users.py####
@pytest.mark.anyio
async def test_read_all_user_comments(client, token):
    response = await client.get(
        f"/api/users/{user_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert type(data) == list


###from routes/images.py####
@pytest.mark.anyio
async def test_create_comment_to_image(client, token):
    response = await client.post(
        f"/api/images/{image_id}/comments",
        json=body,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201, response.text


@pytest.mark.anyio
async def test_update_comment(client, token):
    response = await client.patch(
        f"/api/comments/{comment_id}",
        json=body_test,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text


@pytest.mark.anyio
async def test_delete_comment(client, token):
    response = await client.delete(
        f"/api/comments/{comment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204, response.text
