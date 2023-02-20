from pydantic import BaseModel


"""
Pydantic base models used for accepting HTTP requests data regarding users
"""


class UserIdBaseModal(BaseModel):
    """ A Pydantic base model which includes only a user ID used for querying users"""
    user_id: int


class UserEmailBaseModal(BaseModel):
    """ A Pydantic base model which includes only a user email used for querying users"""
    email: str


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


# For user login

class UserLoginBaseModule(BaseModel):
    """ A Pydantic base model for logging-in a user to the application
    This will be used by CHAT BE microservice in route POST /chat_be/users/login """
    email: str
    password: str


class UserLoginResultBaseModule(BaseModel):
    """ A Pydantic base model for the UM service response for a user login
    This will be used by CHAT BE microservice in route POST /chat_be/users/login

    * is_login_success - bool, true if user succeeded login ( correct email + password )
    * is_active - bool, if user is active or not ( according to DB )
    """
    is_login_success: bool
    is_active: bool
