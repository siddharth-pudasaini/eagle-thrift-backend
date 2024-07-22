from pydantic import BaseModel,Field ,EmailStr
from typing import Optional
from sqlmodel import SQLModel

class UserModel(SQLModel):
    email: EmailStr
    password:str=Field(...,min_length=8)
    username: str = Field(...)

class CategoryModel(SQLModel):
    name:str =Field(...,min_length=1)

class LoginModel(BaseModel):
    email:EmailStr
    password:str=Field(...,min_length=8)

class ListingModel(SQLModel):
    title:str=Field(...,max_length=100,min_length=1)
    description:str=Field(...,max_length=2000,min_length=1)
    price:float=Field(...,ge=0,le=1000000000)
    category:int=Field(...,ge=1)

class AdminIdModel(BaseModel):
    id:str=Field(...)

class CategoryResponse(SQLModel):
    name: str
    id:int

class MessageModel(SQLModel):
    content: str = Field(..., max_length=1000)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    listing_id: int = Field(foreign_key="listing.id")


class ConversationModel(SQLModel):
    listing_id: int = Field(foreign_key="listing.id")
    user_1: int = Field(foreign_key="user.id")
    user_2: int = Field(foreign_key="user.id")