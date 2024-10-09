from typing import List

from sqlalchemy.orm import Session

from app.src.database.models import Tag
from app.src.schemas.users import TagModel


async def get_tags(skip: int, limit: int, db: Session) -> List[Tag]:
    return db.query(Tag).offset(skip).limit(limit).all()


async def get_tag(tag_id: int, db: Session) -> Tag:
    return db.query(Tag).filter(Tag.id == tag_id).first()


async def create_tag(body: TagModel, db: Session) -> Tag:
    tag = Tag(name=body.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


async def update_tag(tag_id: int, body: TagModel, db: Session) -> Tag | None:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        tag .name = body.name
        db.commit()
    return tag


async def remove_tag(tag_id: int, db: Session)  -> Tag | None:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
    return tag
