from pydantic import BaseModel
from pydantic_schemas.user_manager_service_responses_schemas import UserManagerResponseUserDetailsBaseModule


"""
Pydantic schemas for validation of HTTP requests input sent to the CHAT BE microservice
"""


# HTTP requests sent by client
class HTTPRequestUserCreate(BaseModel):
    """ A pydantic schema used for create user HTTP request
    Used at route - /user/create
    """
    email: str
    password: str


class HTTPRequestUserLogin(BaseModel):
    """ A pydantic schema used for create user HTTP request
    Used at route - /user/login
    """
    email: str
    password: str


# HTTP responses received from server
class HTTPResponseUserLogin(BaseModel):
    """ A pydantic schema used for login HTTP response
    Used by route POST /user/login """
    jwt_token: str
    user_details: UserManagerResponseUserDetailsBaseModule
