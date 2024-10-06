"""
Module of contacts' routes
"""


from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session
from app.src.database.models import User
from app.src.repository import contacts as repository_contacts
from app.src.schemas.contacts import ContactModel, ContactResponse
from app.src.services.auth import auth_service


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=List[ContactResponse])
async def read_contacts(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=1000),
    first_name: str = Query(default=None),
    last_name: str = Query(default=None),
    email: str = Query(default=None),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to contacts route and reads a list of contacts for a specific user with specified pagination parameters and search by first name, last name and email.

    :param offset: The number of contacts to skip (default = 0, min value = 0).
    :type offset: int
    :param limit: The maximum number of contacts to return (default = 10, min value = 1, max value = 1000).
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
    return await repository_contacts.read_contacts(
        offset, limit, first_name, last_name, email, user, session
    )


@router.get("/birthdays_in_{n}_days", response_model=List[ContactResponse])
async def read_contacts_with_birthdays_in_n_days(
    n: int = Path(ge=1, le=31),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=1000),
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to '/birthdays_in_{n}_days' contacts subroute and reads a list of contacts with birthdays in n day(s) for a specific user with specified pagination parameters.

    :param n: The number of days to find contacts' birthdays (min value = 1, max value = 31, 1 - only for today)
    :type n: int
    :param offset: The number of contacts to skip (default = 0, min value = 0).
    :type offset: int
    :param limit: The maximum number of contacts to return (default = 10, min value = 1, max value = 1000).
    :type limit: int
    :param user: The user to retrieve contacts for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: A list of contacts with birthdays in n day(s) or None.
    :rtype: List[Contact] | None
    """
    return await repository_contacts.read_contacts_with_birthdays_in_n_days(
        n, offset, limit, user, session
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a GET-operation to '/{contact_id}' contacts subroute and reads a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to retrieve
    :type contact_id: UUID4 | int
    :param user: The user to retrieve contacts for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The contact with the specified ID.
    :rtype: Contact
    """
    contact = await repository_contacts.read_contact(contact_id, user, session)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactModel,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a POST-operation to contacts route and creates a new contact for a specific user.

    :param body: The request body with data for the contact to create.
    :type body: ContactModel
    :param user: The user to create the contact for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The newly created contact.
    :rtype: Contact
    """
    contact = await repository_contacts.create_contact(body, user, session)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The contact's email and/or phone already exist",
        )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID4 | int,
    body: ContactModel,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a PUT-operation to '/{contact_id}' contacts subroute and updates a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to update
    :type contact_id: UUID4 | int
    :param body: The request body with data for the contact to update.
    :type body: ContactModel
    :param user: The user to update the contact for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: The updated contact.
    :rtype: Contact
    """
    contact = await repository_contacts.update_contact(contact_id, body, user, session)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: UUID4 | int,
    user: User = Depends(auth_service.get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Handles a DELETE-operation to '/{contact_id}' contacts subroute and deletes a single contact with the specified ID for a specific user.

    :param contact_id: The ID of the contact to delete
    :type contact_id: UUID4 | int
    :param user: The user to delete the contact for.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: None.
    :rtype: None
    """
    contact = await repository_contacts.delete_contact(contact_id, user, session)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return None