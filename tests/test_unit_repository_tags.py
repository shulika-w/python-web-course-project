import pickle
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import User, Tag
from app.src.repository.tags import read_tags, read_tag, create_tag, delete_tag


class TestTags(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(
            id=1,
            username="test",
            email="test@test.com",
            password="1234567890",
        )
        self.tag = Tag(
            id=1,
            title="test",
        )
        self.session = MagicMock(spec=AsyncSession)

    async def test_create_tag(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.tag
        result = await create_tag(self.tag.title, self.user, self.session)
        self.assertEqual(result.title, self.tag.title)

    async def test_read_tag(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.tag
        result = await read_tag(self.tag.title, self.session)
        self.assertEqual(result, self.tag)

    async def test_read_tags(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = [self.tag]
        result = await read_tags(0, 10, self.tag.title, self.session)
        self.assertEqual(result[0], self.tag)

    async def test_delete_tag(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.tag
        result = await delete_tag(self.tag.title, self.session)
        self.assertEqual(result, self.tag)


if __name__ == "__main__":
    unittest.main()
