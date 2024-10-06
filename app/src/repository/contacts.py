"""
Module of contacts' CRUD
"""


from collections import defaultdict
from datetime import date, timedelta
from pydantic import UUID4
from typing import List

from sqlalchemy import select, and_, or_
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Contact, User
from app.src.schemas.contacts import ContactModel
from app.src.utils.is_leap_year import is_leap_year


async def read_contacts(
    offset: int,
    limit: int,
    first_name: str,
    last_name: str,
    email: str,
    user: User,
    session: AsyncSession,
) -> ScalarResult:
    """
    Reads a list of contacts for a specific user with specified pagination parameters and search by first name, last name and email.

    :param offset: The number of contacts to skip.
    :type offset: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param first_name: The string to search by first name.
    :type first_name: str
    :param last_name: The string to search by last name.
    :type last_name: str
    :param email: The string to search by email.
    :type email: str
    :param user: The user to retrieve contacts for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of contacts or None.
    :rtype: ScalarResult
    """
    stmt = select(Contact).filter(Contact.user_id == user.id)
    if first_name:
        stmt = stmt.filter(Contact.first_name.like(f"%{first_name}%"))
    if last_name:
        stmt = stmt.filter(Contact.last_name.like(f"%{last_name}%"))
    if email:
        stmt = stmt.filter(Contact.email.like(f"%{email}%"))
    stmt = stmt.offset(offset).limit(limit)
    contacts = await session.execute(stmt)
    return contacts.scalars()


async def read_contacts_with_birthdays_in_n_days(
    n: int,
    offset: int,
    limit: int,
    user: User,
    session: AsyncSession,
) -> List[Contact] | None:
    """
    Reads a list of contacts with birthdays in n day(s) for a specific user with specified pagination parameters.

    :param n: The number of days to find contacts' birthdays (1 - only for today)
    :type n: int
    :param offset: The number of contacts to skip.
    :type offset: int
    :param limit: The maximum number of contacts to return.
    :type limit: int
    :param user: The user to retrieve contacts for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of contacts with birthdays in n day(s) or None.
    :rtype: List[Contact] | None
    """
    stmt = select(Contact).filter(Contact.user_id == user.id)
    contacts = await session.execute(stmt)
    contacts = contacts.scalars()
    tmp = defaultdict(list)
    tmp_leap_day = defaultdict(list)
    today_date = date.today()
    is_leap_year_flag = is_leap_year(today_date.year)
    number_of_days_in_the_year = 365 + is_leap_year_flag
    last_date = today_date + timedelta(days=n - 1)
    is_includes_next_year_flag = bool(last_date.year - today_date.year)
    for contact in contacts:
        birthday = contact.birthday
        if not is_leap_year_flag and birthday.month == 2 and birthday.day == 29:
            date_delta = date(year=today_date.year, month=3, day=1) - today_date
            is_leap_day = True
        else:
            date_delta = birthday.replace(year=today_date.year) - today_date
            is_leap_day = False
        delta_days = date_delta.days
        if is_includes_next_year_flag and delta_days < n - number_of_days_in_the_year:
            delta_days += number_of_days_in_the_year
        if 0 <= delta_days < n:
            if is_leap_day:
                tmp_leap_day[delta_days].append(contact)
            else:
                tmp[delta_days].append(contact)
    if tmp_leap_day and tmp:
        for delta_days in range(n):
            if tmp_leap_day.get(delta_days):
                tmp[delta_days] = tmp_leap_day[delta_days] + tmp[delta_days]
    result = []
    if tmp:
        for delta_days in range(n):
            if tmp.get(delta_days):
                result = result + tmp[delta_days]
    return result[offset : offset + limit]


async def read_contact(
    contact_id: UUID4 | int, user: User, session: AsyncSession
) -> Contact | None:
    """
    Reads a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve
    :type contact_id: UUID4 | int
    :param user: The user to retrieve contacts for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The contact with the specified ID, or None if it does not exist.
    :rtype: Contact | None
    """
    stmt = select(Contact).filter(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    contact = await session.execute(stmt)
    return contact.scalar()


async def create_contact(
    body: ContactModel, user: User, session: AsyncSession
) -> Contact | None:
    """
    Creates a new contact for a specific user.

    :param body: The request body with data for the contact to create.
    :type body: ContactModel
    :param user: The user to create the contact for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The newly created contact or None if creation failed.
    :rtype: Contact | None
    """
    stmt = select(Contact).filter(
        and_(
            or_(Contact.email == body.email, Contact.phone == body.phone),
            Contact.user_id == user.id,
        )
    )
    contacts = await session.execute(stmt)
    contacts = contacts.scalars()
    for contact in contacts:
        return None
    contact = Contact(**body.model_dump(), user_id=user.id)
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def update_contact(
    contact_id: UUID4 | int, body: ContactModel, user: User, session: AsyncSession
) -> Contact | None:
    """
    Updates a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update
    :type contact_id: UUID4 | int
    :param body: The request body with data for the contact to update.
    :type body: ContactModel
    :param user: The user to update the contact for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The updated contact or None if it does not exist.
    :rtype: Contact | None
    """
    stmt = select(Contact).filter(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    contact = await session.execute(stmt)
    contact = contact.scalar()
    if contact:
        contact.first_name = body.first_name
        contact.last_name = body.last_name
        contact.email = body.email
        contact.phone = body.phone
        contact.birthday = body.birthday
        contact.address = body.address
        await session.commit()
    return contact


async def delete_contact(
    contact_id: UUID4 | int, user: User, session: AsyncSession
) -> Contact | None:
    """
    Deletes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to delete
    :type contact_id: UUID4 | int
    :param user: The user to delete the contact for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The deleted contact or None if it did not exist.
    :rtype: Contact | None
    """
    stmt = select(Contact).filter(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    contact = await session.execute(stmt)
    contact = contact.scalar()
    if contact:
        await session.delete(contact)
        await session.commit()
    return contact