from typing import Dict, Union, Tuple
from loguru import logger

from pydantic_schemas import request_input_schemas
from utils.jwt_utils import JWTHelper, JWTTokenInvalidException
from constants import JWTTypes, MicroServicesNames


"""
JWT Issue class - which is used by auth service to issue JWT tokens and verify them.
lLl JWT tokens are in a unified format which should be used by all microservices in this project
"""


class MicroserviceAuthenticationTokenInvalidException(Exception):
    """ Raises when a microservice tries to issue a JWT token for itself using a wrong authentication token.
    This exception is used when a microservice tries to issue JWT token ( And not when trying to validate an already
    issued token ) """
    pass


class FailedParsingJWTToken(Exception):
    """ Raises when fails to read a JWT token. This should be used after verifying the JWT token is authenticated so it
    will raise if the JWT token is missing fields. ( "email", "is_active" etc... ) """
    pass




class JWTTokenMicroService:
    """ Represent a microservice JWT token values. This should be created after validating the JWT token. """

    def __init__(self, token_type: str, service_name):
        """

        :param token_type:
        :param service_name:
        """
        self.token_type: str = token_type
        self.service_name: str = service_name


class JWTTokenRegisteredUser:
    """ Represent a registered user JWT token values. This should be created after validating the JWT token. """

    def __init__(self, token_type: str, user_id: str, email: str, is_active: bool):
        """

        :param token_type:
        :param user_id:
        :param email:
        :param is_active:
        """
        self.token_type: str = token_type
        self.user_id: str = user_id
        self.email: str = email
        self.is_active: bool = is_active


class JWTInvalidAuthException(Exception):
    """ Raises when a given JWT token is invalid.
     This exception is used when a microservice tries to authenticate with auth service and uses an invalid token.
     ( And not when a microservice tries to issue a JWT token ) """
    pass


class JWTIssuer:
    """ A class used to issue JWT tokens by the auth_service """

    def __init__(self,
                 private_key: str,
                 public_key: str,
                 expiration_time_in_hours: int,
                 key_algorithm: str):
        """

        :param private_key:
        :param public_key:
        :param expiration_time_in_hours:
        :param key_algorithm:
        """
        self._jwt_helper = JWTHelper(private_key=private_key,
                                     public_key=public_key,
                                     expiration_time_in_hours=expiration_time_in_hours,
                                     key_algorithm=key_algorithm)

    def get_public_key(self) -> str:
        """ Returns the public key used to sign JWT tokens

        :return: str
        """
        return self._jwt_helper.get_public_key()

    def get_key_algorithm(self) -> str:
        """ Returns the key algorithm used to sign JWT tokens

        :return: str
        """
        return self._jwt_helper.get_key_algorithm()

    @staticmethod
    def _authenticate_service_token(micro_service_initial_token: str, micro_service_name: str) -> bool:
        """ Authenticates a microservice token. If microservice is authenticated then the auth servie will issue it a
        JWT token, so it can interact with other service.

        In order for a microservice to get a JWT token, it needs to pass a test proving it is the real microservice in
        front of the authentication service. This is done by providing a token string which is shared between the
        microservice and the authentication_service.

        :param micro_service_initial_token: A string token supplied by a microservice wishing to receive a JWT token
                                            from auth service
        :param micro_service_name: The service name which the microservice wants to have a JWT token for
        :return: bool, true in case initial token is correct for the service
        """
        try:
            if MicroServicesNames.MICROSERVICES_TOKENS_DICT[micro_service_name] == micro_service_initial_token:
                logger.success(f"successfully authenticated as micro-service {micro_service_name}")
                return True
            logger.error("Failed to authenticate in front of auth service - "
                         f"given token for micro service name {micro_service_name} was wrong!")
            return False
        except KeyError:
            logger.error("Failed to authenticate in front of auth service - "
                         f"given service name {micro_service_name} doesn't exist! "
                         f"Available options: {MicroServicesNames.MICROSERVICES_TOKENS_DICT.keys()}")
            return False

    def issue_micro_service_jwt(self,
                                service_auth_details: request_input_schemas.HTTPRequestIssueServiceJWTModel) -> str:
        """ Issues a JWT token for a microservice in the project.

        In order for a microservice to prove its identity it needs to pass a shared token which is injected to both the
        microservice environment and the auth service environment.

        :param service_auth_details:
        :raises MicroserviceAuthenticationTokenInvalidException: In case the microservice sent a wrong token
        :return: JWT token
        """
        if not self._authenticate_service_token(
                micro_service_initial_token=service_auth_details.micro_service_initial_token,
                micro_service_name=service_auth_details.micro_service_name
        ):
            raise MicroserviceAuthenticationTokenInvalidException()
        service_token_payload: Dict[str, any] = {
            "service_name": service_auth_details.micro_service_name,
            **JWTTypes.MICROSERVICE,
        }
        jwt_token: str = self._jwt_helper.sign_token(payload=service_token_payload)
        return jwt_token

    def issue_user_jwt(self, user_details: request_input_schemas.HTTPRequestIssueUserJWTModel) -> str:
        """ Issues a JWT token for a user in the project.

        The function issues the JWT without verifying the authenticity of details, this should be done by the
        microservices who require it.

        :param user_details:
        :return: JWT token
        """
        user_token_payload: Dict[str, any] = {
            "user_id": user_details.user_id,
            "email": user_details.email,
            "is_active": user_details.is_active,
            **JWTTypes.REGISTERED_USER,
        }
        jwt_token: str = self._jwt_helper.sign_token(payload=user_token_payload)
        return jwt_token

    def is_token_valid(self, jwt_token: str) -> bool:
        """ Validates a token is authenticated and valid.

        :param jwt_token:
        :return: bool - true if JWT token is valid
        """
        try:
            self._jwt_helper.validate_token(jwt_token=jwt_token)
            return True
        except JWTTokenInvalidException:
            return False

    @staticmethod
    def _parse_microservice_token(jwt_token_payload: Dict[str, any]) -> JWTTokenMicroService:
        """

        :param jwt_token_payload:
        :raises FailedParsingJWTToken: In case parsing JWT failed ( example - if some fields are missing )
        :return: JWTTokenMicroService which contains JWT details
        """
        try:
            token_type: str = jwt_token_payload["token_type"]
            service_name: str = jwt_token_payload["service_name"]

            microservice_token = JWTTokenMicroService(token_type=token_type,
                                                      service_name=service_name)
            return microservice_token
        except KeyError as exception:
            logger.error(f"Failed parsing microservice JWT token - {jwt_token_payload}, exception: {exception}")
            raise FailedParsingJWTToken()

    @staticmethod
    def _parse_registered_user_token(jwt_token_payload: Dict[str, any]) -> JWTTokenRegisteredUser:
        """

        :param jwt_token_payload:
        :raises FailedParsingJWTToken: In case parsing JWT failed ( example - if some fields are missing )
        :return: JWTTokenRegisteredUser which contains JWT details
        """
        try:
            token_type: str = jwt_token_payload["token_type"]
            user_id: str = jwt_token_payload["user_id"]
            email: str = jwt_token_payload["email"]
            is_active: bool = jwt_token_payload["is_active"]

            user_token = JWTTokenRegisteredUser(token_type=token_type,
                                                user_id=user_id,
                                                email=email,
                                                is_active=is_active)
            return user_token
        except KeyError as exception:
            logger.error(f"Failed parsing registered user JWT token - {jwt_token_payload}, exception: {exception}")
            raise FailedParsingJWTToken()

    def read_jwt_token(self, jwt_token: str) -> Tuple[str, Union[JWTTokenMicroService, JWTTokenRegisteredUser]]:
        """ Read a JWT token issued by the auth service and returns its payload an object representing it. ( Custom
        class which assures JWT token contains all fields needed. )

        :param jwt_token:
        :raises JWTTokenInvalidException: In case token is not valid (bad signature or token expired)
        :raises FailedParsingJWTToken: In case token is valid, but its payload is missing fields ( This is not supposed
                                       to happen and probably means the private key was stolen to fake the JWT )
        :return: Tuple - token type (microservice or registered user) and an object representing the token payload
        """
        try:
            token_payload: Dict[str, any] = self._jwt_helper.validate_token(jwt_token=jwt_token)
            if token_payload["token_type"] == JWTTypes.MICROSERVICE_KEY_VALUE:
                token_details: JWTTokenMicroService = self._parse_microservice_token(jwt_token_payload=token_payload)
                token_type: str = JWTTypes.MICROSERVICE_KEY_VALUE
            elif token_payload["token_type"] == JWTTypes.REGISTERED_USER_KEY_VALUE:
                token_details: JWTTokenRegisteredUser = \
                    self._parse_registered_user_token(jwt_token_payload=token_payload)
                token_type: str = JWTTypes.REGISTERED_USER_KEY_VALUE
            else:
                raise FailedParsingJWTToken()
            return token_type, token_details
        except JWTTokenInvalidException:
            raise JWTInvalidAuthException()
