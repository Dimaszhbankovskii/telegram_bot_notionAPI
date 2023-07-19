from pydantic.main import BaseModel
from uuid import UUID
from datetime import datetime


class Object(BaseModel):
    id: UUID
    object: str


class Parent(BaseModel):
    type: str
    database_id: UUID


class EntryDB(BaseModel):
    object: str
    id: UUID
    created_by: Object
    last_edited_by: Object
    created_time: datetime
    last_edited_time: datetime
    parent: Parent
    properties: dict
