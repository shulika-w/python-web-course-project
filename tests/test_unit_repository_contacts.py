from datetime import date
import unittest
from unittest.mock import MagicMock

from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Contact, User
from app.src.schemas.contacts import ContactModel
from app.src.repository.contacts import (
    read_contacts,
    read_contacts_with_birthdays_in_n_days,
    read_contact,
    create_contact,
    update_contact,
    delete_contact,
)


class TestContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1)
        self.session = MagicMock(spec=AsyncSession)
        self.body = ContactModel(
            first_name="test",
            last_name="test",
            email="test@test.com",
            phone="1234567890",
            birthday=date.today(),
            address="test",
        )

    async def test_read_contacts(self):
        contacts = [Contact(), Contact(), Contact()]
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = contacts
        result = await read_contacts(
            offset=0,
            limit=10,
            first_name=None,
            last_name=None,
            email=None,
            user=self.user,
            session=self.session,
        )
        self.assertEqual(result, contacts)

    async def test_read_contacts_with_birthdays_in_n_days(self):
        contacts = [
            Contact(birthday=date.today()),
            Contact(birthday=date.today()),
            Contact(birthday=date.today()),
        ]
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalars.return_value = contacts
        result = await read_contacts_with_birthdays_in_n_days(
            n=1,
            offset=0,
            limit=10,
            user=self.user,
            session=self.session,
        )
        self.assertEqual(result, contacts)

    async def test_read_contact(self):
        contact = Contact()
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = contact
        result = await read_contact(
            contact_id=contact.id,
            user=self.user,
            session=self.session,
        )
        self.assertEqual(result, contact)

    async def test_read_contact_not_found(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        result = await read_contact(
            contact_id=2,
            user=self.user,
            session=self.session,
        )
        self.assertIsNone(result)

    async def test_create_contact(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        result = await create_contact(
            body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result.first_name, self.body.first_name)
        self.assertEqual(result.last_name, self.body.last_name)
        self.assertEqual(result.email, self.body.email)
        self.assertEqual(result.phone, self.body.phone)
        self.assertEqual(result.birthday, self.body.birthday)
        self.assertEqual(result.address, self.body.address)
        self.assertTrue(hasattr(result, "id"))

    async def test_update_contact_found(self):
        contact = Contact()
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = contact
        result = await update_contact(
            contact_id=contact.id, body=self.body, user=self.user, session=self.session
        )
        self.assertEqual(result, contact)

    async def test_update_contact_not_found(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        result = await update_contact(
            contact_id=2,
            body=self.body,
            user=self.user,
            session=self.session,
        )
        self.assertIsNone(result)

    async def test_delete_contact_found(self):
        contact = Contact()
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = contact
        result = await delete_contact(
            contact_id=contact.id, user=self.user, session=self.session
        )
        self.assertEqual(result, contact)

    async def test_delete_contact_not_found(self):
        self.session.execute.return_value = MagicMock(spec=ChunkedIteratorResult)
        self.session.execute.return_value.scalar.return_value = None
        result = await delete_contact(
            contact_id=2, user=self.user, session=self.session
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()