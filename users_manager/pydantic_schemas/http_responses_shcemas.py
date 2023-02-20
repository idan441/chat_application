from typing import Dict, List
from pydantic import BaseModel
from .users_schemas import UserDetailsBaseModule, UserLoginResultBaseModule


"""
Pydantic base models used for HTTP responses returned
"""


class HTTPTemplateBaseModel(BaseModel):
    """ A basic template for all HTTP responses returned

    All applications HTTP responses should be in this base format.

    HTTP status code is return in this object, and will be later manipulated at middleware level to over-write FastAPI
    status code. This is done to simplify setting status code in this application.
    example:
    { "uuid": 1234, is_success: True , content: { users: ... } }
    """
    uuid: str = "123"
    is_success: bool = True
    text_message: str | None


class HTTPTemplateBaseModelListUsersDetails(HTTPTemplateBaseModel):
    """ Return response for a list of users details """
    content: List[UserDetailsBaseModule]


class HTTPTemplateBaseModelSingleUserDetails(HTTPTemplateBaseModel):
    """ Return response for a single user details """
    content: UserDetailsBaseModule


class HTTPTemplateBaseModelError(HTTPTemplateBaseModel):
    """ Returns an error response for bad HTTP requests with no "content" field value """


class HTTPTemplateBaseModelAdminLoginResponse(HTTPTemplateBaseModel):
    """ Return response for admin login """
    content: Dict


class HTTPTemplateBaseModelUserLoginResponse(HTTPTemplateBaseModel):
    """ Return response for application user login attempts

    This will be used by CHAT BE microservice in route POST /chat_be/users/login , which will send user credentials to
    UM service in order to validate user credentials + assure he is active (un-active users are not allowed to log in!)
    """
    content: UserLoginResultBaseModule

