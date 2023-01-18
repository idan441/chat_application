from datetime import datetime, timedelta, timezone
from typing import Dict
import jwt
from loguru import logger

from pydantic_schemas import request_input_schemas

"""
Includes a class for managing JWT tokens generation and authentication
"""


class JWTTokenInvalidException(Exception):
    """ Raises when a given JWT is invalid """
    pass


class MicroserviceAuthenticationTokenInvalidException(Exception):
    """ Raises when a microservice tries to authenticate with a wrong authentication token """
    pass


class JWTHelper:
    """ Utilities for JWT token creation in the project """

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
        self._private_key: str = private_key
        self._public_key: str = public_key
        self._expiration_time_in_hours: int = expiration_time_in_hours
        self._key_algorithm: str = key_algorithm

    def get_public_key(self) -> str:
        """ Returns the public key used to sign JWT tokens

        :return: str
        """
        return self._public_key

    def get_key_algorithm(self) -> str:
        """ Returns the key algorithm used to sign JWT tokens

        :return: str
        """
        return self._key_algorithm

    def sign_token(self, payload: Dict[str, any]) -> str:
        """ Signs a JWT token

        :param payload:
        :return: JWT token (str)
        """
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(hours=self._expiration_time_in_hours)
        jwt_token: str = jwt.encode(payload=payload, key=self._private_key, algorithm=self._key_algorithm)
        return jwt_token

    def validate_token(self, jwt_token: str) -> Dict:
        """ Validates a token is authenticated and valid

        Checks two factors - 1) JWT signature is correct, 2) JWT expiration date is valid

        :raises JWTTokenInvalidException: In case JWT key is signed with wrong key or has expired
        :return: Dict, the JWT token payload
        """
        try:
            decoded_payload: Dict = jwt.decode(jwt=jwt_token, key=self._public_key, algorithms=[self._key_algorithm])
            return decoded_payload
        except jwt.exceptions.DecodeError:
            logger.error("A JWT token with a bad signature! Someone tried to over-write the signature! ")
            raise JWTTokenInvalidException("Token is not signed correctly")
        except jwt.exceptions.ExpiredSignatureError:
            logger.info("A JWT which is expired was given, please refresh it")
            raise JWTTokenInvalidException("Token has expired")


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

    def _authenticate_service_token(self, micro_service_initial_token: str, micro_service_name: str) -> bool:
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
        # TODO - finish here
        if micro_service_initial_token == "aaaa":
            return True
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
            "token_type": "microservice",
            "service_name": service_auth_details.micro_service_name,
        }
        jwt_token: str = self._jwt_helper.sign_token(payload=service_token_payload)
        return jwt_token

    def issue_user_jwt(self, user_details: request_input_schemas.HTTPRequestIssueUserJWTModel) -> str:
        """ Issues a JWT token for a user in the project.

        THe function issues the JWT without verifying the authenticity of details, this should be done by the
        microservices who require it.

        :param user_details:
        :return: JWT token
        """
        user_token_payload: Dict[str, any] = {
            "token_type": "registered_user",
            "user_id": user_details.user_id,
            "email": user_details.email,
            "is_active": user_details.is_active,
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
