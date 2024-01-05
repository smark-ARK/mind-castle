from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional, List
from datetime import datetime


# * User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    class config:
        orm_mode = True


class UserResponse(UserBase):
    id: int

    class config:
        orm_mode = True


# * AuthSchemas
class ResponseToken(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# * Notes Schemas
class NoteBase(BaseModel):
    title: str
    detail: str


class NoteResponse(NoteBase):
    id: int
    owner_id: int
    owner: UserResponse
    created_at: datetime


class ParticipantInfo(BaseModel):
    user: UserResponse
    permission: str


class NoteResponseWithParticipants(BaseModel):
    note: NoteResponse
    participants: List[ParticipantInfo]


class Permissions(str, Enum):
    read_only = "read_only"
    edit = "edit"


class ShareNote(BaseModel):
    user_id: int
    permission: Permissions = Permissions.read_only


class ShareNoteResponse(BaseModel):
    note: NoteResponse
    user: UserResponse
    permission: str
