from typing import Optional
from pydantic import BaseModel


"""
Pydantic modules for parsing HTTP responses from USER MANAGER service

Used to validate responses from UM service in UserManagerIntegration class at ./utils/user_manager_integrations.py
"""


class UserManagerResponseUserDetailsBaseModule(BaseModel):
    """ Represents UM response for GET /chat_be/user/details/{user_id} route """
    user_id: int
    email: str
    is_active: bool


class UserManagerUserLoginResponseBaseModule(BaseModel):
    """ Represents UM response for POST /chat_be/user/login route

    * is_login_success - bool, true if user succeeded login ( correct email + password )
    * is_active - bool, if user is active or not ( according to DB )
    """
    is_login_success: bool
    is_active: bool
    user_details: Optional[UserManagerResponseUserDetailsBaseModule] = None
