from pydantic import BaseModel,Field as PydanticField ,EmailStr
from typing import Optional
from sqlmodel import Field,SQLModel,Session,select
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from datetime import datetime


from input_models import UserModel,ListingModel

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



class Listing(ListingModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    created_by:Optional[int] | None=Field(default=None,foreign_key="user.id")
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

    