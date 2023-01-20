from datetime import datetime, timedelta, timezone
from typing import Dict
import jwt
from loguru import logger


"""
Includes a class for managing JWT tokens generation and authentication
"""


class JWTTokenInvalidException(Exception):
    """ Raises when a given JWT is invalid """
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
