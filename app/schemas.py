from pydantic import BaseModel, EmailStr
from typing import Optional, List


# * User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    id: int
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


# * Category Schemas
class CategoryBase(BaseModel):
    name: str
    user_id: int


class CategoryResponse(CategoryBase):
    id: int
    user: UserBase

    class config:
        orm_mode = True


# * Notes Schemas
class NoteBase(BaseModel):
    title: str
    detail: str
    category_id: Optional[int] = None


class NoteResponse(NoteBase):
    id: int
    category: Optional[CategoryResponse]
    owner: UserResponse


# class ShareNote(BaseModel):
#     user_id: int
#     permission:
