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


def read_file_content(file_path: str) -> str:
    """ Reads an ASCII text file and returns its content

    :param file_path:
    :return: file content"""
    with open(fr"{file_path}") as file:
        file_content: str = file.read()
    return file_content


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
        self.private_key: str = private_key
        self.public_key: str = public_key
        self.expiration_time_in_hours: int = expiration_time_in_hours
        self.key_algorithm: str = key_algorithm
        print(self.private_key)
        print(self.public_key)

    def get_public_key(self) -> str:
        """ Returns the public key used to sign JWT tokens

        :return: str
        """
        return self.public_key

    def get_key_algorithm(self) -> str:
        """ Returns the key algorithm used to sign JWT tokens

        :return: str
        """
        return self.key_algorithm

    def sign_token(self, payload: Dict[str, any]) -> str:
        """ Signs a JWT token """
        payload["exp"] = datetime.now(tz=timezone.utc) + timedelta(hours=self.expiration_time_in_hours)
        jwt_token: str = jwt.encode(payload=payload, key=self.private_key, algorithm=self.key_algorithm)
        return jwt_token

    def validate_token(self, jwt_token: str) -> Dict:
        """ Validates a token is authenticated and valid

        :raises JWTTokenInvalidException: In case JWT key is signed with wrong key or has expired
        :return: Dict, the JWT token payload
        """
        try:
            decoded_payload: Dict = jwt.decode(jwt=jwt_token, key=self.public_key, algorithms=[self.key_algorithm])
            return decoded_payload
        except jwt.exceptions.DecodeError:
            logger.error("A JWT token with a bad signature! Someone tried to over-write the signature! ")
        except jwt.exceptions.ExpiredSignatureError:
            logger.info("A JWT which is expired was given, please refresh it")
