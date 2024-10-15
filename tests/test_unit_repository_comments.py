import unittest
from unittest.mock import MagicMock

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Comment, User
from app.src.schemas.comments import CommentModel
from app.src.repository.comments import (
    read_all_comments_to_image,
    read_all_comments_to_comment,
    read_all_my_comments,
    read_all_user_comments,
    create_comment_to_image,
    create_comment_to_comment,
    update_comment,
    delete_comment
)


class TestComments(unittest.IsolatedAsyncioTestCase):
    image_id = 1
    comments = [
        Comment(id=1, text="Comment 1", user_id=1, image_id=1, parent_id=None),
        Comment(id=2, text="Comment 2", user_id=2, image_id=1, parent_id=None)
    ]

    def setUp(self):
        self.session = MagicMock(spec=AsyncSession)
        self.user = User(id=1)
        self.comment = Comment(
            text="Comment test",
            user_id=1,
            image_id=1,
            id=1,
            parent_id=None
        )
        self.body = CommentModel(
            text="string11"
        )

    async def test_read_all_comments_to_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.comments
        result = await read_all_comments_to_image(
            image_id=1,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.comments)

    async def test_read_all_comments_to_comment(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.comments
        result = await read_all_comments_to_comment(
            comment_id=1,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.comments)

    async def test_read_all_my_comments(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.comments
        result = await read_all_my_comments(
            user=self.user,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.comments)

    async def test_read_all_user_comments(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.comments
        result = await read_all_user_comments(
            user_id=self.comment.user_id,
            offset=0,
            limit=10,
            session=self.session,
        )
        self.assertEqual(result, self.comments)

    async def test_create_comment_to_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        result = await create_comment_to_image(
            image_id=self.comment.image_id, body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result.text, self.body.text)
        self.assertEqual(result.image_id, self.comment.image_id)
        self.assertEqual(result.user_id, self.comment.user_id)
        self.assertIsNone(result.parent_id)
        self.assertTrue(hasattr(result, "id"))

    async def test_create_comment_to_comment(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.comment
        result = await create_comment_to_comment(
            comment_id=self.comment.id, body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result.text, self.body.text)
        self.assertEqual(result.image_id, self.comment.image_id)
        self.assertEqual(result.user_id, self.comment.user_id)
        self.assertTrue(hasattr(result, "id"))
        self.assertEqual(result.parent_id, self.comment.id)

    async def test_update_comment(self):
        comment = Comment()
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = comment
        result = await update_comment(
            comment_id=self.comment.id, body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result.text, self.body.text)

    async def test_delete_comment(self):
        comment = Comment()
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = comment
        result = await delete_comment(
            comment_id=comment.id, session=self.session
        )
        self.assertEqual(result, comment)
