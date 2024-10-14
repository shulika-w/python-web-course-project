"""
Module of comments' routes
"""

from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session
from app.src.database.models import User, Role
from app.src.repository import rates as repository_rates
from app.src.schemas.rates import RateModel, RateResponse, RateImageResponse
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess

allowed_operation_get = RoleAccess([Role.administrator, Role.moderator, Role.user])
allowed_operation_create = RoleAccess(
    [Role.administrator, Role.moderator, Role.user])
allowed_operation_update = RoleAccess(
    [Role.administrator, Role.moderator, Role.user])
allowed_operation_remove = RoleAccess([Role.administrator, Role.moderator])
allowed_operation_non_user = RoleAccess([Role.administrator, Role.moderator])

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get(
    "/{image_id}",
    response_model=List[RateResponse],
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_all_rates_to_photo(
        image_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of all rates to photo.

    :param image_id: UUID4 | int: Identify the image
    :param offset: int: Skip the first offset number of elements in the list
    :param ge: Set a minimum value for the parameter
    :param limit: int: Limit the number of results returned
    :param ge: Specify the minimum value of a parameter
    :param le: Limit the number of results returned
    :param session: AsyncSession: Get the database session
    :param : Get the rate of a specific user to a photo
    :return: A list of rates
    """

    return await repository_rates.read_all_rates_to_photo(image_id, offset, limit, session)


@router.get(
    "/my/rates",
    response_model=List[RateResponse],
    dependencies=[Depends(allowed_operation_get)],
)
async def read_all_my_rates(
        current_user: User = Depends(auth_service.get_current_user),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of all rates that the current user has created.

    :param current_user: User: Get the current user from the auth_service
    :param offset: int: Specify the number of records to skip
    :param ge: Specify that the offset must be greater than or equal to 0
    :param limit: int: Limit the number of results returned
    :param ge: Ensure that the offset is greater than or equal to 0
    :param le: Limit the number of items returned
    :param session: AsyncSession: Create a new session for the database
    :param : Get the current user
    :return: A list of all the rates created by a user
    """

    return await repository_rates.read_all_my_rates(
        current_user, offset, limit, session
    )


@router.get(
    "/user/rates",
    response_model=List[RateResponse],
    dependencies=[Depends(allowed_operation_non_user)],
)
async def read_all_user_rates(
        user_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of all rates for the user with the given id.

    :param user_id: UUID4 | int: Identify the user
    :param offset: int: Determine the starting point of the query
    :param ge: Check if the value is greater than or equal to a certain number
    :param limit: int: Limit the number of results returned
    :param ge: Specify that the value must be greater than or equal to the given value
    :param le: Limit the number of results returned
    :param session: AsyncSession: Get the session from the dependency injection
    :param : Get the user_id from the path
    :return: A list of rates
    """

    return await repository_rates.read_all_user_rates(
        user_id, offset, limit, session
    )


@router.get(
    "/{image_id}/avg",
    response_model=RateImageResponse,
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_avg_rate_to_photo(
        image_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
):
    """
    Returns the average rate of a photo.

    :param image_id: UUID4 | int: Specify the image_id of the photo to be rated
    :param session: AsyncSession: Pass the session to the repository layer
    :param : Get the average rate of a photo
    :return: The average rate of a photo given its id
    """

    return await repository_rates.read_avg_rate_to_photo(image_id, session)


@router.get(
    "/avg/all",
    response_model=List[RateImageResponse],
    dependencies=[Depends(allowed_operation_get),
                  Depends(auth_service.get_current_user)])
async def read_all_avg_rates(
        session: AsyncSession = Depends(get_session),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
):
    """
    Returns a list of all the average rates in the database.

    :param session: AsyncSession: Get the database session
    :param offset: int: Specify the number of records to skip
    :param ge: Specify a minimum value for the parameter
    :param limit: int: Limit the number of results returned
    :param ge: Specify that the value must be greater than or equal to the given value
    :param le: Limit the number of results returned
    :param : Get the session to be used in the function
    :return: A list of average rates
    """

    return await repository_rates.read_all_avg_rates(offset, limit, session)


@router.post(
    "/{image_id}",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)])
async def create_rate_to_photo(
        image_id: UUID4 | int,
        body: RateModel,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session)):
    """
    Creates a new rate to photo.

    :param image_id: UUID4 | int: Specify the image that will be rated
    :param body: RateModel: Get the rate from the request body
    :param current_user: User: Get the current user from the auth_service
    :param session: AsyncSession: Pass the session to the repository layer
    :return: A ratemodel object
    """

    rate = await repository_rates.create_rate_to_photo(image_id, body, current_user, session)
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or forbidden to rate twice or forbidden to rate your photo"
        )
    return rate


@router.delete(
    "/{rate_id}",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create),
                  Depends(auth_service.get_current_user)])
async def delete_rate_to_photo(
        rate_id: UUID4 | int,
        session: AsyncSession = Depends(get_session)):
    """
    Deletes a rate to photo.

    :param rate_id: UUID4 | int: Specify the rate id that will be deleted
    :param session: AsyncSession: Pass the session to the repository
    :return: A boolean value
    """

    return await repository_rates.delete_rate_to_photo(rate_id, session)
