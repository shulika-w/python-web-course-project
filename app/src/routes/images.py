"""
Module of images' routes
"""

from typing import List

from pydantic import UUID4
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import FileResponse
from redis.asyncio.client import Redis
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.connect_db import get_session, get_redis_db1
from app.src.database.models import User, Role
from app.src.repository import comments as repository_comments
from app.src.repository import images as repository_images
from app.src.repository import rates as repository_rates
from app.src.schemas.comments import CommentModel, CommentResponse
from app.src.services.auth import auth_service
from app.src.services.roles import RoleAccess
from app.src.services.qr_code import generate_qr_code
from app.src.schemas.images import (
    ImageModel,
    ImageDb,
    ImageDescriptionModel,
    CloudinaryTransformations,
)
from app.src.schemas.rates import RateModel, RateResponse, RateImageResponse

router = APIRouter(prefix="/images", tags=["images"])

allowed_operations_for_self = RoleAccess(
    [Role.administrator, Role.moderator, Role.user]
)
allowed_operations_for_moderate = RoleAccess([Role.administrator, Role.moderator])
allowed_operations_for_all = RoleAccess([Role.administrator])


@router.post(
    "",
    response_model=ImageDb,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def create_image(
        data: ImageModel = Depends(ImageModel.as_form),
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a POST-operation to "" images subroute and create an image.

    :param file: The uploaded file to create avatar from.
    :type file: UploadFile
    :param data: The data for the image to create.
    :type data: ImageCreateForm
    :param user: The user who creates the image.
    :type user: User
    :param session: Get the database session
    :type AsyncSession: The current session.
    :param cache: The Redis client.
    :type cache: Redis
    :return: Newly created image of the current user.
    :rtype: Image
    """
    image = await repository_images.create_image(data, user, session, cache)
    return image


@router.get(
    "/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_image(
        image_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/{image_id}' images subroute and gets the image with id.

    :param image_id: The image id.
    :type image_id: UUID | int
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: The image with id.
    :rtype: Image
    """
    image = await repository_images.read_image(image_id, session, cache)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return image


@router.get(
    "/{image_id}/qr_code",
    response_class=FileResponse,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def get_qr_code(
        image_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a GET-operation to '/{image_id}/qr_code' images subroute and gets FileResponse.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param session: Get the database session
    :type AsyncSession: The current session.
    :return: Reply with a file in image/png format.
    :rtype: FileResponse
    """
    image = await repository_images.read_image(image_id, session, cache)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    image_url = image.url
    generate_qr_code(image_url)
    return FileResponse(
        "static/qrcode.png",
        media_type="image/png",
        filename="qrcode.png",
        status_code=200,
    )


@router.get(
    "",
    response_model=List[ImageDb],
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_images(
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
) -> ScalarResult:
    """
    Handles a GET-operation to images route and gets images of current user.

    :param user: The current user.
    :type user: User
    :return: List of images of the current user.
    :rtype: ScalarResult
    """
    images = await repository_images.read_images(user.id, session)
    return images


@router.put(
    "/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def update_image(
        image_id: UUID4 | int,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
        transformations: List[CloudinaryTransformations] = Query(
            ...,
            description="""List of Cloudinary image transformations:
        
        none = ""
        crop (make avatar with face)= "c_thumb,g_face,h_200,w_200,z_1/f_auto/r_max/",
        resize (downscaling)= "ar_1.0,c_fill,h_250",
        rotate (turn 10 degrees clockwise [0-360])= "a_10/",
        improve = "e_improve:outdoor:29/",
        brightness = "e_brightness:80/",
        blackwhite = "e_blackwhite:49/",
        saturation = "e_saturation:50/",
        border = "bo_10px_solid_lightblue/",
        rounded_corners = "r_100/"
        """,
        ),
):
    """
    Handles a PUT operation for the images subroute '/{image_id}'.
        Updates the current user's image.

    :param image_id: The Id of the image.
    :type image_id: UUID4 | int
    :param user: The current user who updated image.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :param transformations: The Enum list of the image file transformation parameters.
    :type transformations: List
    :return: The updated image object.
    :rtype: Image
    """
    image = await repository_images.update_image(
        image_id,
        transformations,
        user.id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.patch(
    "/{image_id}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def patch_image(
        image_id: UUID4 | int,
        body: ImageDescriptionModel,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{image_id}'.
        Patches the current user's image.

    :param image_id: The Id of the image to patch.
    :type image_id: UUID4 | int
    :param body: The data for the image to patch.
    :type body: ImageDescriptionModel
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :param transformations: The Enum list of the image file transformation parameters.
    :type transformations: List
    :return: The updated image.
    :rtype: Image
    """
    image = await repository_images.patch_image(
        image_id,
        body,
        user.id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def delete_image(
        image_id: UUID4 | int,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Handles a DELETE operation for the images subroute '/{image_id}'.
        Deleted the current user's image.

    :param image_id: The Id of the image to delete.
    :type image_id: UUID4 | int
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: None
    :type: None
    """
    image = await repository_images.delete_image(image_id, user.id, session)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return None


@router.patch(
    "/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def add_tag_to_image(
        image_id: UUID4 | int,
        tag_title: str,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a PATCH operation for the images subroute '/{image_id}/tags/{tag_title}'.
        Patches the tags of the current user's image.

    :param image_id: The Id of the image to patch.
    :type image_id: UUID4 | int
    :param tag_title: The tag title for the image.
    :type tag_title: str
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :return: Patched image object.
    :type: Image
    """
    image = await repository_images.add_tag_to_image(
        image_id,
        tag_title,
        user.id,
        user,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.delete(
    "/{image_id}/tags/{tag_title}",
    response_model=ImageDb,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def delete_tag_from_image(
        image_id: UUID4 | int,
        tag_title: str,
        user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
        cache: Redis = Depends(get_redis_db1),
):
    """
    Handles a DELETE operation for the images subroute '/{image_id}/tags/{tag_title}'.
        Delited the current user's image tag.

    :param image_id: The Id of the image to delete.
    :type image_id: UUID4 | int
    :param tag_title: The tag title for the image.
    :type tag_title: str
    :param user: The current user.
    :type user: User
    :param session: The database session.
    :type session: AsyncSession
    :param cache: The Redis client.
    :type cache: Redis
    :return: An image object.
    :rtype: Image
    """
    image = await repository_images.delete_tag_from_image(
        image_id,
        tag_title,
        user.id,
        session,
        cache,
    )
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
    return image


@router.get(
    "/{image_id}/comments",
    response_model=List[CommentResponse],
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_all_comments_to_image(
        image_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of comments for the specified image.

    :param image_id: UUID4 | int: Specify the image id of the image to which we want to add a comment
    :param offset: int: Specify the offset from which to start returning comments
    :param ge: Set a minimum value for the parameter
    :param limit: int: Limit the amount of comments that are returned
    :param ge: Specify the minimum value for a parameter
    :param le: Limit the number of comments returned
    :param user: User: Get the current user
    :param session: AsyncSession: Create a new session to the database
    :param : Get the user who is logged in
    :return: A list of comments to the image
    """
    return await repository_comments.read_all_comments_to_image(
        image_id, offset, limit, session
    )


@router.post(
    "/{image_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def create_comment_to_image(
        image_id: UUID4 | int,
        body: CommentModel,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Creates a comment to an image.

    :param image_id: UUID4 | int: Specify the image id that the comment will be added to
    :param body: CommentModel: Create a comment to the image
    :param current_user: User: Get the current user from the auth_service
    :param session: AsyncSession: Pass the session to the repository layer
    :return: A comment
    """
    return await repository_comments.create_comment_to_image(
        image_id, body, current_user, session
    )


@router.get(
    "/{image_id}/rates",
    response_model=List[RateResponse],
    dependencies=[
        Depends(allowed_operations_for_moderate),
    ],
)
async def read_all_rates_to_image(
        image_id: UUID4 | int,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=1000),
        session: AsyncSession = Depends(get_session),
):
    """
    Returns a list of all rates to image.

    :param image_id: UUID4 | int: Identify the image
    :param offset: int: Skip the first offset number of elements in the list
    :param ge: Set a minimum value for the parameter
    :param limit: int: Limit the number of results returned
    :param ge: Specify the minimum value of a parameter
    :param le: Limit the number of results returned
    :param session: AsyncSession: Get the database session
    :param : Get the rate of a specific user to a image
    :return: A list of rates
    """

    return await repository_rates.read_all_rates_to_image(
        image_id, offset, limit, session
    )


@router.post(
    "/{image_id}/rates",
    response_model=RateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def create_rate_to_image(
        image_id: UUID4 | int,
        body: RateModel,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    Creates a new rate to image.

    :param image_id: UUID4 | int: Specify the image that will be rated
    :param body: RateModel: Get the rate from the request body
    :param current_user: User: Get the current user from the auth_service
    :param session: AsyncSession: Pass the session to the repository layer
    :return: A ratemodel object
    """

    rate = await repository_rates.create_rate_to_image(
        image_id, body, current_user, session
    )
    if rate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or forbiden to rate twice or forbidden to rate your image",
        )
    return rate


@router.get(
    "/{image_id}/avg",
    response_model=RateImageResponse,
    dependencies=[Depends(allowed_operations_for_self)],
)
async def read_avg_rate_to_image(
        image_id: UUID4 | int,
        session: AsyncSession = Depends(get_session),
        # cache: Redis = Depends(get_redis_db1),#####
):
    """
    Returns the average rate of a image given its id.

    :param image_id: UUID4 | int: Specify the image_id of the image to be rated
    :param session: AsyncSession: Pass the session to the repository layer
    :param cache: Redis: Get the average rate of a image
    :param : Get the rate of a image
    :return: The average rate of a image given its id
    """
    return await repository_rates.read_avg_rate_to_image(image_id, session)  ######, cache)
