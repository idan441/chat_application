from typing import Dict
from loguru import logger

from pydantic_schemas import request_input_schemas
from utils.jwt_utils import JWTHelper, JWTTokenInvalidException


"""
JWT Issue class - which is used by auth service to issue JWT tokens and verify them.
lLl JWT tokens are in a unified format which should be used by all microservices in this project
"""


class MicroserviceAuthenticationTokenInvalidException(Exception):
    """ Raises when a microservice tries to authenticate with a wrong authentication token """
    pass


class JWTTypes:
    """ Constants used for a field called "token_type" which is used to differ different token types issued by the
    auth service. These values should be used to evaluate JWT tokens by other microservices using the auth service """
    REGISTERED_USER: Dict[str, str] = {"token_type": "registered_user"}
    MICROSERVICE: Dict[str, str] = {"token_type": "microservice"}


class MicroServicesNames:
    """ List of registered microservices which can authenticate with auth service """
    USERS_MANAGER = "user_manager"
    CHAT_BE = "chat_be"

    """ Authentication tokens used by different microservices int eh project in order to authenticate with auth service
        and issue a JWT token for themselves. """
    MICROSERVICES_TOKENS_DICT: Dict[str, str] = {

        USERS_MANAGER: "aaa",
        CHAT_BE: "aaaa",
    }


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
