
from sqlmodel import SQLModel,create_engine,Session

from starlette.config import Config

from db_schema import User

config=Config(".env")

#Database details
_user = config("USER", cast=str)
_password = config("PASSWORD", cast=str)
_host = config("HOST", cast=str)
_database = config("DATABASE", cast=str)
_port = config("PORT", cast=int, default=3306)



engine=create_engine(f'sqlite:///./api.db',echo=True)
SQLModel.metadata.create_all(engine)

User.register_listeners()

def get_session():
    with Session(engine) as session:
        yield session

