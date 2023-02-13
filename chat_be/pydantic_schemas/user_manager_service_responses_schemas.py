from pydantic import BaseModel


"""
Pydantic modules for parsing HTTP responses from USER MANAGER service

Used to validate responses from UM service in UserManagerIntegration class at ./utils/user_manager_integrations.py
"""


class UserManagerResponseUserDetailsBaseModule(BaseModel):
    """ Represents UM response for GET /chat_be/user/{user_id} route """
    user_id: int
    email: str
    is_active: bool
