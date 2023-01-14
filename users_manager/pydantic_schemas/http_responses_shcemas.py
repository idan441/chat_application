from typing import Dict, Union, List
from pydantic import BaseModel
from .users_schemas import UserDetailsBaseModule


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


class HTTPTemplateBaseModelAdminLoginResponse(HTTPTemplateBaseModel):
    """ Return response for admin login """
    content: Dict
