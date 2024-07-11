from pydantic import EmailStr
from typing import Optional
from sqlmodel import Field,SQLModel,Session,select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from datetime import datetime


from input_models import UserModel,ListingModel,CategoryModel

class TimeStampedData(SQLModel):
    created_at: Optional[datetime] = Field(default=None, nullable=False)
    updated_at: Optional[datetime] = Field(default=None, nullable=False)


class User(UserModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    email: EmailStr=Field(...,unique=True)
    phone_number:Optional[str]=Field(None,min_length=10)

    @classmethod
    def create(cls, session: Session, user: "User") -> str:
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return {f'User with email {user.email} created successfully'}
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))

    @classmethod
    def get_user(cls,email:EmailStr, session: Session):
        statement=select(cls).where(cls.email==email)
        user=session.exec(statement).first()
        if user:
            return user
        raise HTTPException(status_code=404,detail="User not found")

class Category(CategoryModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    name:str=Field(...,nullable=False,unique=True)
    item_count:Optional[int]=Field(default=0)

    @classmethod
    def create(cls, session: Session, category: "Category") -> str:
        try:
            session.add(category)
            session.commit()
            session.refresh(category)
            return {f'{category.name} created successfully'}
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))


class Listing(ListingModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    created_by:int=Field(default=None,foreign_key="user.id",nullable=False)
    category:int=Field(default=0,foreign_key="category.id",nullable=False)
    @classmethod
    def create(cls,user:int,session:Session,listing:"Listing")->str:
        listing.created_by=user
        try:
            session.add(listing)
            session.commit()
            session.refresh(listing)
            return(f'Listing created')
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))

    @classmethod   
    def get_single_listing(cls,id:int,session:Session):
        listing = session.get(cls, id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return listing



