from pydantic import BaseModel


"""
Pydantic base models for users table in the MySQL DB of CHAT BE microservice
"""


class UserIdBaseModal(BaseModel):
    """ A Pydantic base model which includes only a user ID used for querying users"""
    user_id: int


class UserEmailBaseModal(BaseModel):
    """ A Pydantic base model which includes only a user email used for querying users"""
    email: str


class UserCreateBaseModule(BaseModel):
    """ A Pydantic base model for creating a new user """
    user_id: int
    email: str


class UserUpdateBaseModule(BaseModel):
    """ A pydantic base model for updating an existing user in CHAT BE users table
     Note - updating user_id or email is prohibited, and if in need - should be done also in USER MANAGER user. Doing
     that will be in another base module. """
    user_id: int
    nickname: str | None
    text_status: str | None

