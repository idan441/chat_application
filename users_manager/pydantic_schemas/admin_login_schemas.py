from pydantic import BaseModel


"""
Pydantic base models used for accepting HTTP requests data regarding admin login details
"""


class LoginDetailsModal(BaseModel):
    """ A Pydantic base model for admin login details """
    username: str
    password: str
