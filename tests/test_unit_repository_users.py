import pickle
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import User
from app.src.schemas.users import UserModel, UserUpdateModel
from app.src.repository.users import (
    get_user_by_email_from_cache,
    get_user_by_email,
    get_user_by_username,
    create_user,
    update_user,
    confirm_email,
    reset_password,
    set_password,
    set_role_for_user,
    activate_user,
    inactivate_user,
)
from app.src.services._cloudinary import cloudinary_service


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
        self.new_user = User(
            id=2,
            username="new_test",
            email="new_test@test.com",
            password="1234567890",
            role="User",
            is_email_confirmed=False,
            is_password_valid=True,
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

    async def test_get_user_by_username(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.user
        result = await get_user_by_username(self.user.username, self.session)
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

    async def test_update_user(self):
        body = UserUpdateModel(
            first_name="test",
            last_name="test",
            phone="1234567890",
            birthday="2001-01-01",
            avatar=MagicMock(),
        )
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.user
        self.redis_db.expire.return_value = None
        avatar_url = "http://test.com/avatar"
        cloudinary_service.upload_avatar = AsyncMock()
        cloudinary_service.upload_avatar.return_value = avatar_url
        result = await update_user(self.user.email, body, self.session, self.redis_db)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.phone, body.phone)
        self.assertEqual(result.birthday, body.birthday)
        self.assertEqual(result.avatar, avatar_url)

    async def test_confirm_email(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.new_user
        await confirm_email(self.new_user.email, self.session, self.redis_db)
        self.assertTrue(self.new_user.is_email_confirmed)

    async def test_reset_password(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.new_user
        await reset_password(self.new_user.email, self.session, self.redis_db)
        self.assertFalse(self.new_user.is_password_valid)

    async def test_set_password(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.new_user
        new_password = "0987654321"
        await set_password(
            self.new_user.email, new_password, self.session, self.redis_db
        )
        self.assertTrue(self.new_user.is_password_valid)
        self.assertEqual(self.new_user.password, new_password)

    async def test_set_role_for_user(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.new_user
        role = "Moderator"
        result = await set_role_for_user(
            self.new_user.username, role, self.session, self.redis_db
        )
        self.assertEqual(result.role, role)

    async def test_inactivate_user(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.new_user
        result = await inactivate_user(self.user.username, self.session, self.redis_db)
        self.assertFalse(result.is_active)

    async def test_activate_user(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.new_user
        result = await activate_user(self.user.username, self.session, self.redis_db)
        self.assertTrue(result.is_active)


if __name__ == "__main__":
    unittest.main()
