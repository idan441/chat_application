from typing import List, Optional

from utils.jwt_validator import AuthServiceJWTValidator, JWTInvalidAuthException, FailedParsingJWTToken
from pydantic_schemas.jwt_token_schemas import JWTTokenRegisteredUser, JWTTokenMicroService
from constants import JWTTypes


"""
Includes AuthHTTPRequest class which handles verifying authentication of using sending requests to auth service using
FastAPI framework.

Note - this class is based on the one with the same name in AUTH SERVICE microservice code - but this one uses
       AuthServiceJWTValidator objects for functionalities! It is not the same code as in AUTH SERVICE but similar!
"""


class AuthorizationHeaderInvalidHeaderFormat(Exception):
    """ Raises when AuthHTTPRequest fails to parse an "Authorization Bearer" header because its value is wrong and not
    according to standards.
    Authorization header structure for bearer tokens (=JWT tokens) is - "Authorization: Bearer <JWT token>"
    Example: missing the word "Bearer" or having an empty JWT token attached. """


class AuthorizationHeaderInvalidToken(Exception):
    """ Raises when AuthHTTPRequest fails to read the JWT token attached to it. This can happen from two reasons:
    1) JWT token is signed with a wrong private key. ( Note - in such case make sure PEM key-pairs weren't stolen! )
    2) JWT token has expired. ( In such case the registered user or microservice need to issue a new JWT token )

    If this exception raises - that means the authorization bearer header is formatted correct and that the issue is
    related only to JWT token authenticity.
    """


class AuthorizationHeaderJWTTokenNotPermitted(Exception):
    """ Raises when a given JWT is not permitized to use the FastAPI route. This raises by AuthHTTPRequest after
    successfully reading the authorization header and verifying the JWT authenticity. This error is related to
    permission not satisfied for the microservice or registered using sending the JWT token."""


class AuthHTTPRequest:
    """ A class which will be used to check and read HTTP requests headers sent by clients, verifying their identity
    by reading the JWT token attached. """
    AUTHORIZATION_HEADER_NAME: str = "Authorization"

    def __init__(self, jwt_validator: AuthServiceJWTValidator):
        """

        :param jwt_validator: A JWT validator object which handles JWT validation in front of AUTH SERVICE
        """
        self.jwt_validator: AuthServiceJWTValidator = jwt_validator

    @staticmethod
    def parse_auth_bearer_header(authorization_bearer_header: str) -> str:
        """ Parses value of Authorization bearer header assuring it is valid according to standard - "Bearer <token>"

        :param authorization_bearer_header: str, should be "Bearer <JWT-token>"
        :raises AuthorizationHeaderInvalidHeaderFormat: If the authorization header is invalid
        :return: the JWT token itself
        """
        try:
            header_values: List[str] = str(authorization_bearer_header).split(" ")
            auth_type: str = header_values[0]
            token: str = header_values[1]
        except IndexError:
            raise AuthorizationHeaderInvalidHeaderFormat("Authorization token is too short and missing parts")

        if len(header_values) != 2:
            raise AuthorizationHeaderInvalidHeaderFormat("Authorization token has too many parts")
        if auth_type != "Bearer":
            raise AuthorizationHeaderInvalidHeaderFormat("Authorization token missing 'Bearer' in its beginning")
        if len(token) < 1:
            raise AuthorizationHeaderInvalidHeaderFormat("Token attached to authorization token is empty "
                                                         "and has less than 1 char")

        return token

    def verify_micro_service_jwt_token(self, authorization_bearer_header: str,
                                       micro_service_name: Optional[str] = None) -> JWTTokenMicroService:
        """ Verifies if a microservice type JWT token is attached to the HTTP request sent to FastAPI.

        This will check if the JWT token is recognized as a microservice JWT token. ( An internal decision in this
        project - all JWT tokens will include a "token_type" field with a value - "microservice" or "registered_user" )

        :param authorization_bearer_header:
        :param micro_service_name: Optional - microservice name, this will verify the JWT token is sent by a specific
                                   microservice name. ( Will check if field "service_name" has service name value )
        :raises AuthorizationHeaderInvalidToken: In case the JWT token is invalid
        :raises AuthorizationHeaderJWTTokenNotPermitted: In case the JWT token is not a microservice JWT token
        :return:
        """
        jwt_token: str = self.parse_auth_bearer_header(authorization_bearer_header=authorization_bearer_header)

        try:
            token_type, jwt_token_payload_object = self.jwt_validator.read_jwt_token(jwt_token=jwt_token)
        except (FailedParsingJWTToken, JWTInvalidAuthException):
            raise AuthorizationHeaderInvalidToken("Failed reading the JWT token!")

        if token_type != JWTTypes.MICROSERVICE_KEY_VALUE:
            raise AuthorizationHeaderJWTTokenNotPermitted()
        elif micro_service_name is not None:
            if not jwt_token_payload_object.service_name == micro_service_name:
                raise AuthorizationHeaderJWTTokenNotPermitted()
        else:
            return jwt_token_payload_object

    def verify_registered_user_jwt_token(self, authorization_bearer_header) -> JWTTokenRegisteredUser:
        """ Verifies if a registered_user type JWT token is attached to the HTTP request sent to FastAPI.

        This will check if the JWT token is recognized as a microservice JWT token. ( An internal decision in this
        project - all JWT tokens will include a "token_type" field with a value - "microservice" or "registered_user" )

        This method will check the "Authorization" header and will verify it is correctly given - a proper JWT token
        authorization header should be like "Authorization: Bearer <jwt token>"

        :param authorization_bearer_header: the full "Authorization" header sent by a client to the application.
        :raises AuthorizationHeaderInvalidToken: In case the JWT token is invalid
        :raises AuthorizationHeaderJWTTokenNotPermitted: In case the JWT token is not a registered user JWT token
        :return: The JWT token details as JWTTokenRegisteredUser pydantic object
        """
        jwt_token: str = self.parse_auth_bearer_header(authorization_bearer_header=authorization_bearer_header)
        try:
            token_type, jwt_token_payload_object = self.jwt_validator.read_jwt_token(jwt_token=jwt_token)
        except (FailedParsingJWTToken, JWTInvalidAuthException):
            raise AuthorizationHeaderInvalidToken("Failed reading the JWT token!")

        if token_type != JWTTypes.REGISTERED_USER_KEY_VALUE:
            raise AuthorizationHeaderJWTTokenNotPermitted()
        else:
            return jwt_token_payload_object
