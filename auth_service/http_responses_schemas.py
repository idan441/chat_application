from pydantic import BaseModel
from request_input_schemas import HTTPRequestIssueServiceJWTModel


"""
Base models for HTTP response returned by the auth service application
"""


class HTTPTemplateBaseModel(BaseModel):
    """ A basic template for all HTTP responses returned by the auth_service

    All applications HTTP responses should be in this base format.

    HTTP status code is return in this object, and will be later manipulated at middleware level to over-write FastAPI
    status code. This is done to simplify setting status code in this application.
    example:
    { "uuid": 1234, is_success: True , content: { users: ... } }
    """
    uuid: str = "123"
    is_success: bool = True
    text_message: str = ""


class HTTPTemplateBaseModelPublicKey(HTTPTemplateBaseModel):
    """ Return response with the public key used to authenticate JWT tokens signed by the auth_service """
    public_key: str
    key_format_algorithm: str


class HTTPTemplateBaseModelJWTToken(HTTPTemplateBaseModel):
    """ Return response with a JWT token issued by the auth_service """
    jwt_token: str


class HTTPTemplateBaseModelJWTTokenValidation(HTTPTemplateBaseModel):
    """ Return response with validation test result of a JWT token supposedly issued by the auth_service """
    is_jwt_valid: bool


class HTTPTemplateBaseModelJWTTokenIssueFailedValidation(HTTPTemplateBaseModel):
    """ Return response when a microservice JWT token request is rejected because of a wrong token given to
    auth_service """
    given_authentication_details: HTTPRequestIssueServiceJWTModel
