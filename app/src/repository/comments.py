"""
Module of comments' CRUD
"""

from pydantic import UUID4
from sqlalchemy import select, and_
from sqlalchemy.engine.result import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.src.database.models import Comment, User
from app.src.schemas.comments import CommentModel


async def read_all_comments_to_photo(image_id: UUID4 | int, session: AsyncSession) -> list[Comment]:
    stmt = select(Comment)
    stmt = stmt.filter(Comment.image_id == image_id)
    comments = await session.execute(stmt)
    return comments.scalars()


async def create_comment(image_id: UUID4 | int, body: CommentModel, user: User,
                         session: AsyncSession) -> Comment | None:
    comment = Comment(image_id=image_id, text=body.text, user_id=user.id)
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment


async def create_to_comment(comment_id: UUID4 | int, body: CommentModel, user: User,
                            session: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter(Comment.id == comment_id)
    parent_comment = await session.execute(stmt)
    parent_comment = parent_comment.scalar()
    if not parent_comment.parent_id:
        comment = Comment(image_id=parent_comment.image_id, text=body.text, user_id=user.id,
                          parent_id=parent_comment.id)
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment
    return None


async def update_comment(comment_id: UUID4 | int, body: CommentModel, user: User,
                         session: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter(
        and_(Comment.id == comment_id, Comment.user_id == user.id)
    )
    comment = await session.execute(stmt)
    comment = comment.scalar()
    if comment:
        comment.text = body.text
        await session.commit()
    return comment


async def delete_comment(comment_id: UUID4 | int, user: User, session: AsyncSession) -> Comment | None:
    stmt = select(Comment).filter(Comment.id == comment_id)
    comment = await session.execute(stmt)
    comment = comment.scalar()
    if comment:
        await session.delete(comment)
        await session.commit()
    return comment
