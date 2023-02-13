from pydantic import BaseModel


"""
Pydantic schemas for validation of HTTP requests input sent to the CHAT BE microservice
"""


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
