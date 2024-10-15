"""
Module of comments' routes
"""

from pydantic import UUID4
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.src.database.connect_db import get_session
from app.src.database.models import User, Role
from app.src.repository import rates as repository_rates
from app.src.schemas.rates import RateResponse, RateImageResponse
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess

allowed_operations_for_self = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_for_moderate = RoleAccess([Role.administrator, Role.moderator])

router = APIRouter(prefix="/rates", tags=["rates"])


@router.get(
    "",
    response_model=List[RateResponse],
    dependencies=[Depends(allowed_operations_for_self)],
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
    "/avg_all",
    response_model=List[RateImageResponse],
    dependencies=[Depends(allowed_operations_for_moderate)],
)
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
    :param ge: Specify a minimum value for the parameter
    :param le: Limit the number of results returned
    :param : Specify the number of records to skip
    :return: A list of all the average rates in the database
    """
    return await repository_rates.read_all_avg_rates(offset, limit, session)


@router.delete(
    "/{rate_id}",
    response_model=RateResponse,
    dependencies=[Depends(allowed_operations_for_moderate)],
)
async def delete_rate_to_image(
        rate_id: UUID4 | int, session: AsyncSession = Depends(get_session)
):
    """
    Deletes a rate to image.

    :param rate_id: UUID4 | int: Specify the rate id that will be deleted
    :param session: AsyncSession: Pass the session to the repository
    :return: A boolean value
    """
    rate = await repository_rates.delete_rate_to_image(rate_id, session)
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
