import pickle
import unittest
from unittest.mock import MagicMock

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import User
from app.src.schemas.users import UserModel
from app.src.repository.users import (
    get_user_by_email_from_cache,
    get_user_by_email,
    create_user,
    update_avatar,
)


class MockRedis:
    async def get(*args):
        pass

    async def set(*args):
        pass

    async def expire(*args):
        pass


class TestUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(
            id=1,
            username="test",
            email="test@test.com",
            password="1234567890",
        )
        self.session = MagicMock(spec=AsyncSession)
        self.redis_db = MagicMock(spec=MockRedis)

    async def test_get_user_by_email_from_cache(self):
        user = pickle.dumps(self.user)
        self.redis_db.get.return_value = user
        result = await get_user_by_email_from_cache(self.user.email, self.redis_db)
        self.assertEqual(result.id, self.user.id)
        self.assertEqual(result.email, self.user.email)

    async def test_get_user_by_email(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.user
        result = await get_user_by_email(self.user.email, self.session)
        self.assertEqual(result, self.user)

    async def test_create_user(self):
        body = UserModel(username="test", email="test@test.com", password="1234567890")
        self.redis_db.set.return_value = None
        self.redis_db.expire.return_value = self.user
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.all.return_value = None
        result = await create_user(body, self.session, self.redis_db)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_avatar(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.user
        self.redis_db.expire.return_value = None
        url = "http://test.com/avatar"
        result = await update_avatar(self.user.email, url, self.session, self.redis_db)
        self.assertEqual(result.avatar, url)


if __name__ == "__main__":
    unittest.main()