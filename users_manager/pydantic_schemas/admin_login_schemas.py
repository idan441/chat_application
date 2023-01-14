from pydantic import BaseModel


"""
Pydantic base models used for accepting HTTP requests data regarding admin login details
"""


class LoginDetailsModal(BaseModel):
    """ A Pydantic base model for admin login details, used to send HTTP request for login """
    username: str
    password: str
