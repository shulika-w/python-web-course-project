"""
Module with declaring of SQLAlchemy models
"""


from datetime import datetime, date
import enum

from sqlalchemy import (
    UUID,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Date,
    Boolean,
    Enum,
    UniqueConstraint,
    func,
    text,
    Column,
    Integer,
    String,
    Boolean,
    func,
    Table
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base
from app.src.conf.config import settings


Base = declarative_base()

note_m2m_tag = Table(
    "note_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    created_at = Column('created_at', DateTime, default=func.now())
    description = Column(String(150), nullable=False)
    done = Column(Boolean, default=False)
    tags = relationship("Tag", secondary=note_m2m_tag, backref="notes")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)


class Role(enum.Enum):
    administrator: str = "administrator"
    moderator: str = "moderator"
    user: str = "user"


class Contact(Base):
    __tablename__ = "contacts"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint("user_id", "email", name="uix_email"),
        UniqueConstraint("user_id", "phone", name="uix_phone"),
    )
    id: Mapped[UUID | int] = (
        mapped_column(Integer, primary_key=True)
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), primary_key=True, default=text("gen_random_uuid()")
        )
    )
    first_name: Mapped[str] = mapped_column(String(254), nullable=False)
    last_name: Mapped[str] = mapped_column(String(254), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=True)
    phone: Mapped[str] = mapped_column(String(38), nullable=True)
    birthday: Mapped[date] = mapped_column(Date())
    address: Mapped[str] = mapped_column(String(254), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    user_id: Mapped[UUID | int] = (
        mapped_column(Integer, ForeignKey("users.id", onupdate="CASCADE"))
        if settings.test
        else mapped_column(
            UUID(as_uuid=True), ForeignKey("users.id", onupdate="CASCADE")
        )
    )
    user: Mapped["User"] = relationship("User", back_populates="contacts")

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.last_name


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
    refresh_token: Mapped[str] = mapped_column(String(1024), nullable=True)
    is_email_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_password_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    contacts: Mapped["Contact"] = relationship("Contact", back_populates="user")