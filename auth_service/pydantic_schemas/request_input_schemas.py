from pydantic import BaseModel


"""
Base models for HTTP request input for auth service application
"""


class HTTPRequestIssueServiceJWTModel(BaseModel):
    """ A pydantic scheme for HTTP requests used by microservices to issue a JWT token for themselves

     Used by API route /issue_service_jwt
     """
    micro_service_initial_token: str
    micro_service_name: str


class HTTPRequestIssueUserJWTModel(BaseModel):
    """ A pydantic scheme for HTTP requests used to issue a JWT token for registered users. ( Request will be forwarded
    by one of hte microservices in the project )

     Used by API route /sign_user_jwt
     """
    user_id: int
    email: str
    is_active: bool


class HTTPRequestValidateJWTTokenModel(BaseModel):
    """ A pydantic scheme for HTTP requests used to validate a JWT token issued by auth service

     Used by API route /validate_jwt_token
     """
    jwt_token: str
