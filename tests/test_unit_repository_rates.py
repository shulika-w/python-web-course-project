from datetime import datetime
import unittest
import pytest
import asyncio

from unittest.mock import MagicMock, AsyncMock, patch

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Rate, User, Image
from app.src.schemas.rates import RateModel, RateImageResponse
from app.src.repository.rates import (
    read_all_rates_to_image,
    read_all_my_rates,
    read_all_user_rates,
    read_avg_rate_to_image,
    read_all_avg_rates,
    create_rate_to_image,
    delete_rate_to_image
)


class TestComments(unittest.IsolatedAsyncioTestCase):
    rates = [
        Rate(id=1, rate=4, user_id=1, image_id=1),
        Rate(id=2, rate=5, user_id=2, image_id=1)
    ]
    image_ids = [1, 2, 3]
    avg_rates = [4.5, 4.0, 3.5]
    images = [
        Image(id=id, url=f"http://example{id}.com", user_id=1, created_at=datetime.now(), updated_at=datetime.now()) for
        id in image_ids]

    def setUp(self):
        self.session = MagicMock(spec=AsyncSession)
        self.user = User(id=1)
        self.rate = Rate(
            rate=5,
            user_id=1,
            image_id=1,
            id=1,
        )
        self.body = RateModel(
            rate=self.rates[0].rate
        )
        self.image_id = 1
        self.offset = 0
        self.limit = 10
        self.test_avg_rate = 4.5
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)

    async def test_read_all_rates_to_image(self):
        self.session.execute.return_value.scalars.return_value = self.rates
        result = await read_all_rates_to_image(
            image_id=self.image_id,
            offset=self.offset,
            limit=self.limit,
            session=self.session,
        )
        self.assertEqual(result, self.rates)

    async def test_read_all_my_rates(self):
        self.session.execute.return_value.scalars.return_value = self.rates
        result = await read_all_my_rates(
            user=self.user,
            offset=self.offset,
            limit=self.limit,
            session=self.session,
        )
        self.assertEqual(result, self.rates)

    async def test_read_all_user_rates(self):
        self.session.execute.return_value.scalars.return_value = self.rates
        result = await read_all_user_rates(
            user_id=self.user.id,
            offset=self.offset,
            limit=self.limit,
            session=self.session,
        )
        self.assertEqual(result, self.rates)

    async def test_create_rate_to_image(self):
        self.session.execute.return_value.scalar.return_value = None
        result = await create_rate_to_image(
            image_id=self.rates[0].image_id, body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result.rate, self.rates[0].rate)
        self.assertEqual(result.image_id, self.rates[0].image_id)
        self.assertEqual(result.user_id, self.rates[0].user_id)
        self.assertTrue(hasattr(result, "id"))

    async def test_delete_rate_to_photo(self):
        rate = Rate()
        self.session.execute.return_value.scalar.return_value = rate
        result = await delete_rate_to_image(
            rate_id=rate.id, session=self.session
        )
        self.assertEqual(result, rate)

    async def test_read_avg_rate(self):
        test_image = self.images[1]
        avg_rate_mock = MagicMock()
        avg_rate_mock.scalar.return_value = self.test_avg_rate
        image_mock = MagicMock()
        image_mock.scalar.return_value = test_image
        self.session.execute.side_effect = [avg_rate_mock, image_mock]
        result = await read_avg_rate_to_image(self.image_id, self.session)

        assert result.avg_rate == self.test_avg_rate
        assert result.image.id == test_image.id

    async def test_read_all_avg(self):
        async def execute_mock(*args, **kwargs):
            mock = MagicMock()
            mock.scalars.return_value = MagicMock(all=MagicMock(return_value=asyncio.Future()))
            mock.scalars.return_value.all().set_result(self.image_ids)
            return mock

        self.session.execute = execute_mock
        with patch("src.repository.rates.read_avg_rate_to_image",
                   AsyncMock(side_effect=lambda image_id, _:
                   RateImageResponse(image=self.images[image_id - 1],
                                     avg_rate=self.avg_rates[image_id - 1]))):
            result = await read_all_avg_rates(0, 3, self.session)

            for rate_response, expected_rate, expected_image in zip(result, self.avg_rates, self.images):
                assert rate_response.avg_rate == expected_rate
                assert rate_response.image.id == expected_image.id
