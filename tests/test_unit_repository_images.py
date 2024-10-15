import os
import pickle
import sys
from typing import Annotated
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi import UploadFile, File
from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.conf.config import settings
from app.src.database.models import Image, User, Tag
from app.src.services._cloudinary import cloudinary_service
import app.src.repository.tags as repository_tags
from app.src.schemas.images import (
    ImageModel,
    ImageDescriptionModel,
    CloudinaryTransformations,
    MAX_NUMBER_OF_TAGS_PER_IMAGE,
)
from app.src.repository.images import (
    set_image_in_cache,
    create_image,
    read_images,
    read_image,
    update_image,
    patch_image,
    delete_image,
    add_tag_to_image,
    delete_tag_from_image,
)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(project_root)
sys.path.append(project_root)


class MockRedis:
    async def get(*args):
        pass

    async def set(*args):
        pass

    async def expire(*args):
        pass


class TestUsersRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.image = Image(
            id=1,
            user_id=1,
            url="http://test.com/upload/image.png",
        )

        self.user = User(id=1)
        self.tag = Tag(
            id=1,
            title="test",
        )

        self.session = AsyncMock(spec=AsyncSession)
        self.redis_db = MagicMock(spec=MockRedis)

    async def test_set_image_in_cache(self):
        image_id = 1
        await set_image_in_cache(self.image, self.redis_db)
        self.redis_db.set.assert_called_once_with(
            f"image: {image_id}", pickle.dumps(self.image)
        )
        self.redis_db.expire.assert_called_once_with(
            f"image: {image_id}", settings.redis_expire
        )

    async def test_create_image(self):
        file_mock = MagicMock(spec=UploadFile(File("image.png")))
        body = ImageModel(
            file=file_mock,
            description="test",
            tags=["test"],
        )
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        self.redis_db.expire.return_value = None
        image_url = "http://test.com/upload/image.png"
        cloudinary_service.upload_image = AsyncMock()
        result = {"secure_url": "http://test.com/upload/image.png"}
        cloudinary_service.upload_image.return_value = result
        cloudinary_service.get_image_url = AsyncMock()
        cloudinary_service.get_image_url.return_value = image_url

        # image = Image(description=body.description, url=image_url, user_id=self.user.id)
        # self.session.execute.return_value.scalar.return_value = image
        repository_tags.read_tag = AsyncMock()
        repository_tags.read_tag.return_value = None
        repository_tags.create_tag = AsyncMock()
        repository_tags.create_tag.return_value = "test"
        result = await create_image(body, self.user, self.session, self.redis_db)

        self.assertEqual(result.description, body.description)
        self.assertEqual(result.user_id, self.user.id)
        self.assertTrue(hasattr(result, "id"))
        self.assertTrue(hasattr(result, "created_at"))

        result = self.session.add.call_args[0][0]
        self.assertEqual(result.description, body.description)
        # self.assertEqual(result.url, image_url)
        self.assertEqual(result.user_id, self.user.id)

        # Перевіряємо, чи теги були додані до об'єкта Image
        # repository_tags.read_tag.assert_called_once_with("test", self.session)
        # repository_tags.create_tag.assert_called_once_with(
        # "tag_title", self.user, self.session
        # )
        # self.assertEqual(result.tags, [repository_tags.create_tag.return_value])
        # set_image_in_cache.assert_called_once_with(result, self.redis_db)

    async def test_read_images(self):
        self.images = [Image(id=1, user_id=1), Image(id=2, user_id=1)]
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = self.images
        result = await read_images(self.user.id, self.session)
        self.assertEqual(result, self.images)
        stmt = self.session.execute.call_args[0][0]

    async def test_read_image(self):
        image = pickle.dumps(self.image)
        self.redis_db.get.return_value = image
        result = await read_image(self.image.id, self.session, self.redis_db)
        self.assertEqual(result.id, self.image.id)

    async def test_update_image(self):
        self.tranfsormations = CloudinaryTransformations("a_10/")
        self.cloudinary = MagicMock(spec=cloudinary_service.image_transformations)
        self.image.url = "http://test.com/upload/a_10/image.png"

        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.image
        result = await update_image(
            self.image.id,
            self.tranfsormations,
            self.user.id,
            self.session,
            self.redis_db,
        )
        self.assertEqual(result.url, self.image.url)

    async def test_patch_image(self):
        self.body = ImageDescriptionModel(description="new test")
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.image
        result = await patch_image(
            self.image.id, self.body, self.user.id, self.session, self.redis_db
        )
        self.assertEqual(result.description, self.body.description)

    async def test_delete_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = self.image
        result = await delete_image(self.image.id, self.user.id, self.session)
        self.assertEqual(result, self.image)

    async def test_add_tag_to_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.side_effect = [self.image, self.tag]
        tag_title = "test"
        result = await add_tag_to_image(
            self.image.id,
            tag_title,
            self.user.id,
            self.user,
            self.session,
            self.redis_db,
        )
        self.assertEqual(result, self.image)
        self.assertEqual(result.tags, self.image.tags)
        self.assertEqual(result.tags[0].title, tag_title)
        assert len(self.image.tags) <= MAX_NUMBER_OF_TAGS_PER_IMAGE

    async def test_delete_tag_from_image(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.side_effect = [self.image, self.tag]
        self.tag_title = "test"
        result = await delete_tag_from_image(
            self.image.id, self.tag_title, self.user.id, self.session, self.redis_db
        )
        self.assertEqual(result, self.image)
        self.assertEqual(result.tags, self.image.tags)
        self.assertListEqual(result.tags, [])


if __name__ == "__main__":
    unittest.main()
