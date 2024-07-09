from pydantic import BaseModel,Field ,EmailStr
from typing import Optional
from sqlmodel import SQLModel

class UserModel(SQLModel):
    email: EmailStr
    password:str=Field(...,min_length=8)
    full_name: str = Field(...)

class LoginModel(BaseModel):
    email:EmailStr
    password:str=Field(...,min_length=8)

class ListingModel(SQLModel):
    title:str=Field(...,max_length=10,min_length=1)
    description:str=Field(...,max_length=2000,min_length=1)
    price:float=Field(...,ge=0,le=1000000000)

class LoginModel(BaseModel):
    email:EmailStr
    password:str=Field(...,min_length=8)