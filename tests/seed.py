import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import asyncio

import faker
from httpx import AsyncClient

from app.src.conf.config import settings


EMAIL = ""
PASSWORD = ""

NUMBER_OF_CONTACTS = 1000

fake_data = faker.Faker("uk_UA")


async def get_fake_contacts():
    for _ in range(NUMBER_OF_CONTACTS):
        yield {
            "first_name": fake_data.first_name(),
            "last_name": fake_data.last_name(),
            "email": fake_data.email(),
            "phone": fake_data.phone_number(),
            "birthday": fake_data.date(),
            "address": fake_data.address(),
        }


async def send_data_to_api() -> None:
    client = AsyncClient(
        base_url=f"{settings.api_protocol}://{settings.api_host}:{settings.api_port}"
    )
    response = await client.post(
        "/api/auth/login",
        data={"username": EMAIL, "password": PASSWORD},
    )
    data = response.json()
    ACCESS_TOKEN = data["access_token"]
    headers = {
        "content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }
    async for json in get_fake_contacts():
        try:
            await client.post(
                "/api/contacts",
                headers=headers,
                json=json,
            )
        except Exception as error_message:
            print(f"Connection error: {str(error_message)}")
    await client.aclose()
    print("Done")


if __name__ == "__main__":
    asyncio.run(send_data_to_api())