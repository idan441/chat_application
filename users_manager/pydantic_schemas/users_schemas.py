from pydantic import BaseModel


"""
Pydantic base models used for accepting HTTP requests data regarding users
"""


class UserIdBaseModal(BaseModel):
    """ A Pydantic base model which includes only a user ID used for querying users"""
    user_id: int


class UserCreateBaseModule(BaseModel):
    """ A Pydantic base model for creating a new user """
    email: str
    password: str


class UserUpdateBaseModule(BaseModel):
    """ A Pydantic base model for updating an existing user """
    user_id: int
    email: str | None
    password: str | None
    is_active: bool | None


class UserDetailsBaseModule(BaseModel):
    """ A Pydantic base model used to return HTTP responses with user details """
    user_id: int
    email: str
    is_active: bool

    class Config:
        orm_mode = True
