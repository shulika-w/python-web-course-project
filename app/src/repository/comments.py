"""
Module of comments' CRUD
"""

from pydantic import UUID4
from sqlalchemy import select, and_, desc, func
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.database.models import Comment, User
from app.src.schemas.comments import CommentModel


async def read_all_comments_to_photo(
        image_id: UUID4 | int,
        offset: int,
        limit: int,
        session: AsyncSession) -> ScalarResult:
    """
    Returns a list of comments that are associated with the image_id
    parameter. The offset and limit parameters are used to paginate the results.

    :param image_id: UUID4 | int: Specify the image to which we want to get comments
    :param offset: int: Specify the number of rows to skip
    :param limit: int: Limit the number of comments returned
    :param session: AsyncSession: Pass the session to the function
    :return: A list of comments
    """
    stmt = select(Comment).filter(
        and_(Comment.image_id == image_id,
             Comment.parent_id == None)
    )
    stmt = stmt.order_by(desc(Comment.created_at))
    stmt = stmt.offset(offset).limit(limit)
    comments = await session.execute(stmt)

    return comments.scalars()

async def read_all_comments_to_comment(
        comment_id: UUID4 | int,
        offset: int,
        limit: int,
        session: AsyncSession) -> list[Comment] | None:
    """
    Returns all comments to a comment.

    :param comment_id: UUID4 | int: Specify the comment_id of the parent comment
    :param offset: int: Specify the offset of the comments to be returned
    :param limit: int: Limit the number of comments returned
    :param session: AsyncSession: Pass the session to the function
    :return: A list of comments
    """
    stmt = select(Comment).filter(Comment.parent_id == comment_id)
    stmt = stmt.order_by(desc(Comment.created_at))
    stmt = stmt.offset(offset).limit(limit)
    comments = await session.execute(stmt)
    return comments.scalars()

async def read_all_my_comments(
        user: User,
        offset: int,
        limit: int,
        session: AsyncSession) -> ScalarResult:
    """
    Returns a list of comments that the user has made.
    The function takes in an offset and limit to paginate through results.

    :param user: User: Identify the user who is making the request
    :param offset : int: Specify the number of rows to skip
    :param limit: int: Limit the number of comments returned
    :param session: AsyncSession: Pass the database session to the function
    :return: A list of comments
    """
    stmt = select(Comment).filter(Comment.user_id == user.id)
    stmt = stmt.order_by(desc(Comment.created_at))
    stmt = stmt.offset(offset).limit(limit)
    comments = await session.execute(stmt)
    return comments.scalars()

async def read_all_user_comments(
        user_id: UUID4 | int,
        offset: int,
        limit: int,
        session: AsyncSession) -> ScalarResult:
    """
    Returns a list of comments for the user with the given id.
    The function takes in an offset and limit to paginate through results.

    :param user_id: UUID4 | int: Specify the user_id of the comments to be returned
    :param offset : int: Specify the number of rows to skip
    :param limit: int: Limit the number of comments returned
    :param session: AsyncSession: Pass in the session object
    :return: A list of comments
    """
    stmt = select(Comment).filter(Comment.user_id == user_id)
    stmt = stmt.order_by(desc(Comment.created_at))
    stmt = stmt.offset(offset).limit(limit)
    comments = await session.execute(stmt)
    return comments.scalars()


async def read_top_comments_to_photo(
        image_id: UUID4 | int,
        offset: int,
        limit: int,
        session: AsyncSession) -> ScalarResult:
    """
    Returns a list of top(popular) comments to the photo.

    :param image_id: UUID4 | int: Specify the image for which comments are requested
    :param offset: int: Specify the number of records to skip
    :param limit: int: Limit the number of records returned
    :param session: AsyncSession: Pass the database session to the function
    :return: A list of comment objects
    """

    child_count_subq = (
        select(Comment.parent_id, func.count().label("num_children"))
        .where(Comment.parent_id.isnot(None))
        .filter(Comment.image_id == image_id)
        .group_by(Comment.parent_id)
        .subquery()
    )

    query = (select(
        Comment,
        func.coalesce(child_count_subq.c.num_children, 0).label('num_children')
    )
    .outerjoin(child_count_subq, Comment.id == child_count_subq.c.parent_id)
    .where(Comment.parent_id.is_(None))
    .filter(Comment.image_id == image_id)
    .order_by(func.coalesce(child_count_subq.c.num_children, 0).desc()))

    query = query.offset(offset).limit(limit)
    comme = await session.execute(query)
    return comme.scalars()

async def create_comment_to_photo(image_id: UUID4 | int, body: CommentModel, user: User,
                                  session: AsyncSession) -> Comment | None:
    comment = Comment(image_id=image_id,
                      text=body.text,
                      user_id=user.id)
    session.add(comment)
    """
    Creates a comment to an image.
    
    :param image_id: UUID4 | int: Specify the image that the comment is being made on
    :param body: CommentModel: Create a new comment object
    :param user: User: Get the user_id from the user object
    :param session: AsyncSession: Create a new comment object in the database
    :return: A comment object
    """
    await session.commit()
    await session.refresh(comment)
    return comment


async def create_comment_to_comment(comment_id: UUID4 | int, body: CommentModel, user: User,
                                    session: AsyncSession) -> Comment | None:
    """
    Creates a comment to an existing comment.

    :param comment_id: UUID4 | int: Specify the id of the comment that is being replied to
    :param body: CommentModel: Get the text of the comment
    :param user: User: Check if the user is logged in
    :param session: AsyncSession: Create a session to the database
    :return: A comment object or none
    """
    stmt = select(Comment).filter(Comment.id == comment_id)
    parent_comment = await session.execute(stmt)
    parent_comment = parent_comment.scalar()
    if not parent_comment.parent_id:
        comment = Comment(
            image_id=parent_comment.image_id,
            text=body.text,
            user_id=user.id,
            parent_id=parent_comment.id
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment
    return None

async def update_comment(comment_id: UUID4 | int, body: CommentModel, user: User,
                         session: AsyncSession) -> Comment | None:
    """
    Updates existing comment

    :param comment_id: UUID4 | int: Find the comment to update
    :param body: CommentModel: Get the text from the request body
    :param user: User: Check if the user is allowed to delete the comment
    :param session: AsyncSession: Pass the current session to the function
    :return: A comment or none
    """
    stmt = select(Comment).filter(
        and_(Comment.id == comment_id, Comment.user_id == user.id)
    )
    comment = await session.execute(stmt)
    comment = comment.scalar()
    if comment:
        comment.text = body.text
        await session.commit()
    return comment


async def delete_comment(comment_id: UUID4 | int, session: AsyncSession) -> Comment | None:
    """
    Deletes a comment from the database.

    :param comment_id: UUID4 | int: Specify the id of the comment to delete
    :param user: User: Check if the user is authorized to delete the comment
    :param session: AsyncSession: Pass the session to the function
    :return: The comment object that was deleted
    """
    stmt = select(Comment).filter(Comment.id == comment_id)
    comment = await session.execute(stmt)
    comment = comment.scalar()
    if comment:
        await session.delete(comment)
        await session.commit()
    return comment
