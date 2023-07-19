from pydantic.main import BaseModel
from uuid import UUID
from datetime import datetime


class Object(BaseModel):
    id: UUID
    object: str


class Title(BaseModel):
    type: str
    plain_text: str | None


class Description(BaseModel):
    type: str
    plain_text: str | None


class Parent(BaseModel):
    type: str
    page_id: UUID


class Database(BaseModel):
    object: str
    id: UUID
    created_by: Object
    last_edited_by: Object
    created_time: datetime
    last_edited_time: datetime
    title: list[Title]
    description: list[Description]
    properties: dict[str, dict]
    parent: Parent
