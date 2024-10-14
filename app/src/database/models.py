"""
Module with declaring of SQLAlchemy models
"""

import asyncio
from datetime import datetime, date
import enum
from typing import List

import nest_asyncio
from sqlalchemy import (
    UUID,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Date,
    Boolean,
    Enum,
    CheckConstraint,
    Table,
    Column,
    select,
    func,
    text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import async_object_session
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

from app.src.conf.config import settings


Base = declarative_base()


def async_in_sync(func):
    async def wrapped(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapped


class Role(enum.Enum):
    administrator: str = "administrator"
    moderator: str = "moderator"
    user: str = "user"


image_tag_m2m = Table(
    "image_tag_m2m",
    Base.metadata,
    Column("image_id", ForeignKey("images.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[UUID | int] = (
        mapped_column(Integer, primary_key=True)
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
        )
    )
    username: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(60), nullable=False)
    first_name: Mapped[str] = mapped_column(String(254), nullable=True)
    last_name: Mapped[str] = mapped_column(String(254), nullable=True)
    phone: Mapped[str] = mapped_column(String(38), nullable=True)
    birthday: Mapped[date] = mapped_column(Date(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    avatar: Mapped[str] = mapped_column(String(254), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    is_email_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_password_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    images: Mapped[List["Image"]] = relationship("Image", back_populates="user")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="user")
    tags: Mapped[List["Tag"]] = relationship("Tag", back_populates="user")
    rates: Mapped[List["Rate"]] = relationship("Rate", back_populates="user")

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name

    @hybrid_property
    def is_active(self):
        return self.is_email_confirmed or self.is_password_valid


class Image(Base):
    __tablename__ = "images"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[UUID | int] = (
        mapped_column(Integer, primary_key=True)
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
        )
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    user_id: Mapped[UUID | int] = (
        mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
        )
    )
    user: Mapped["User"] = relationship("User", back_populates="images")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="image")
    tags: Mapped[List["Tag"]] = relationship(
        secondary=image_tag_m2m, back_populates="images"
    )
    rates: Mapped[List["Rate"]] = relationship("Rate", back_populates="image")

    @hybrid_property
    def rate(self):
        async def rate_async(self):
            session = async_object_session(self)
            stmt = select(func.avg(Rate.rate)).where(Rate.image_id == self.id)
            rate = await session.execute(stmt)
            return rate.scalar()

        loop = asyncio.get_running_loop()
        nest_asyncio.apply(loop)
        rate = loop.run_until_complete(rate_async(self))
        return rate


class Comment(Base):
    __tablename__ = "comments"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (CheckConstraint("parent_id != id", name="check_parent_id"),)
    id: Mapped[UUID | int] = (
        mapped_column(Integer, primary_key=True)
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
        )
    )
    text: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    user_id: Mapped[UUID | int] = (
        mapped_column(
            Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        )
        if settings.test
        else mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        )
    )
    user: Mapped["User"] = relationship("User", back_populates="comments")
    image_id: Mapped[UUID | int] = (
        mapped_column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE")
        )
    )
    image: Mapped["Image"] = relationship("Image", back_populates="comments")
    parent_id: Mapped[UUID | int] = (
        mapped_column(Integer, ForeignKey("comments.id"), nullable=True)
        if settings.test
        else mapped_column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)
    )
    parent = relationship("Comment", back_populates="children", remote_side=[id])
    children = relationship("Comment", back_populates="parent")


class Tag(Base):
    __tablename__ = "tags"
    __mapper_args__ = {"eager_defaults": True}
    id: Mapped[UUID | int] = (
        mapped_column(Integer, primary_key=True)
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
        )
    )
    title: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_id: Mapped[UUID | int] = (
        mapped_column(
            Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        )
        if settings.test
        else mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        )
    )
    user: Mapped["User"] = relationship("User", back_populates="tags")
    images: Mapped[List["Image"]] = relationship(
        secondary=image_tag_m2m, back_populates="tags"
    )

    def __str__(self):
        return f"#{self.title}"


class Rate(Base):
    __tablename__ = "rates"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (CheckConstraint("rate >= 1 AND rate <= 5", name="check_rate"),)
    id: Mapped[UUID | int] = (
        mapped_column(Integer, primary_key=True)
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
        )
    )
    rate: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    user_id: Mapped[UUID | int] = (
        mapped_column(
            Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
        )
        if settings.test
        else mapped_column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        )
    )
    user: Mapped["User"] = relationship("User", back_populates="rates")
    image_id: Mapped[UUID | int] = (
        mapped_column(Integer, ForeignKey("images.id", ondelete="CASCADE"))
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE")
        )
    )
    image: Mapped["Image"] = relationship("Image", back_populates="rates")