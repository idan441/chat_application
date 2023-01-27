from time import sleep
from typing import Dict, Optional, Literal
from datetime import datetime, timedelta
import requests
import jwt
from loguru import logger

from pydantic_schemas.jwt_token_schemas import JWTTokenMicroService


"""
Defines a class which can validate JWT tokens issued by the AUTH SERVICE
Public key which is needed to validate the JWT tokens will be read from AUTH SERVICE

This class will use JWTReader class which is located at file .utils/jwt_reader.py in order to validate the tokens
"""


class JWTTokenInvalidException(Exception):
    """ Raises when a given JWT is invalid """
    pass


class FailedGettingAuthServiceResponseException(Exception):
    """ Raises when trying to query AUTH SERVICE, and it is not available or returns a bad response."""
    pass


class FailedInitializingAuthServiceJWTValidatorClassException(Exception):
    """ Will raise in case AuthServiceJWTValidator class failed initializing.
    This can happen due to many reasons mainly related to AUTH SERVIE response.

    Initializing is critical for application functionality and in most cases if this exception raises - application will
    terminate """
    pass


class AuthServiceJWTValidator:
    """ Validates JWT tokens issued by AUTH SERVICE
    JWT tokens should follow the format used in the project. """

    def __init__(self,
                 auth_service_address: str,
                 auth_service_get_public_key_api_route: str,
                 auth_service_get_microservice_jwt_token_api_route: str):
        """

        :param auth_service_address:
        :param auth_service_get_public_key_api_route:
        :param auth_service_get_microservice_jwt_token_api_route:
        """
        # AUTH SERVICE endpoints addresses
        self.auth_service_address: str = auth_service_address
        self.auth_service_get_public_key_api_route: str = auth_service_get_public_key_api_route
        self.auth_service_get_microservice_jwt_token_api_route: str = auth_service_get_microservice_jwt_token_api_route

        # Will be set at method initial_jwt_validator()
        self._public_key: Optional[str] = None
        self._key_algorithm: Optional[str] = None
        self._microservice_jwt_token: Optional[str] = None
        self._microservice_jwt_token_expire_datetime: Optional[datetime] = None

    def initial_jwt_validator(self) -> None:
        """ Will initialize the class, by getting the public key from AUTH SERVICE.

        Notes - * you must run this initial method before using the class!
                * in case of error the method will try multiple times to initialize, if fails will raise exception.

        Method will set following variables -
        * self._public_key: str
        * self._key_algorithm: str
        * self._microservice_jwt_token: str

        :raises FailedInitializingAuthServiceJWTValidatorClassException: In case initialization failed.
        :return: None, but will raise an exception if fails to get details from AUTH SERVICE
        """
        attempts: int = 0
        max_attempts: int = 3

        while attempts < max_attempts:
            try:
                self._set_public_key_from_auth_service()
                self._get_microservice_jwt_token_from_auth_service()
                logger.success("Successfully finished JWT validation initiation!")
                return None
            except FailedGettingAuthServiceResponseException:
                logger.critical(f"Failed initializing JWT validator! Attempt {attempts} from {max_attempts}")
                sleep(10)

        logger.critical(f"Failed initializing JWT validator!!! Failed after {attempts} attempts!")
        raise FailedInitializingAuthServiceJWTValidatorClassException()

    def get_microservice_jwt(self) -> str:
        """ Will return the microservice JWT token, so it cna be used by application to contact other microservices in
        the project.

        If microservice JWT token has expired, it will auto-renew it.

        :return: JWT token
        """
        # JWT token must be valid when read by other services, so it should be considered expired a minute before
        jwt_real_expire_time: datetime = datetime.utcnow() - timedelta(minutes=1)
        if self._microservice_jwt_token_expire_datetime < jwt_real_expire_time:
            self._get_microservice_jwt_token_from_auth_service()
        return self._microservice_jwt_token

    def _query_auth_service_api(self, api_route: str, method: Literal["GET", "POST"]) -> Dict[str, any]:
        """ Queries AUTH SERVICE API, and returns the result as a dictionary.

        :param api_route:
        :param method: HTTP method to query AUTH SERVICE API
        :raises FailedGettingAuthServiceResponseException: In case AUTH SERVICE is not available, or the returned
                                                           response is not 200 or JSON valid
        :return: dictionary based on JSON response from AUTH SERVICE
        """
        get_public_key_endpoint: str = f"{self.auth_service_address}/{api_route}"
        try:
            request = requests.request(
                method=method,
                url=get_public_key_endpoint,
             )
        except requests.exceptions.RequestException as e:
            logger.critical(f"Failed getting public key from AUTH SERVICE! Returned error: {e}")
            raise FailedGettingAuthServiceResponseException()

        status_code: int = request.status_code
        if 200 <= status_code <= 299:
            logger.critical(f"AUTH SERVICE returned a bad HTTP response with status code {status_code}")
            raise FailedGettingAuthServiceResponseException()

        try:
            auth_service_response: Dict[str, any] = request.json()
        except ValueError:
            logger.critical(f"Failed parsing the JSON response from AUTH_SERVICE! ")
            raise FailedGettingAuthServiceResponseException()

        return auth_service_response

    def _get_microservice_jwt_token_from_auth_service(self) -> None:
        """ Will get a JWT token for the microservice, so it can authenticate in front of other microservices in the
        project.

        The JWT token will be issued by AUTH SERVICE. Authentication is based on a shared secret string between current
        service and the AUTH SERVICE.

        This method will set variables -
        * self._microservice_jwt_token: str - the JWT token itself
        * self._microservice_jwt_token_expire_datetime: datetime - time when JWT token will expire

        :raises FailedGettingAuthServiceResponseException: If fails to get 200 response from AUTH SERVICE
        :return: None
        """
        try:
            auth_service_response: Dict[str, any] = self._query_auth_service_api(
                method="POST",
                api_route=self.auth_service_get_microservice_jwt_token_api_route
            )
        except FailedGettingAuthServiceResponseException:
            logger.info("Failed getting microservice JWT token from AUTH SERVICE API!")
            raise FailedGettingAuthServiceResponseException()

        try:
            self._microservice_jwt_token: str = auth_service_response["jwt_token"]

            jwt_token_expire_unix_time: int = self.validate_token(jwt_token=self._microservice_jwt_token)["exp"]
            self._microservice_jwt_token_expire_datetime = datetime.utcfromtimestamp(jwt_token_expire_unix_time)
        except KeyError:
            logger.critical("Wrong JSON response from AUTH_SERVICE!"
                            f"Missing field microservice_jwt_token - returned response: {auth_service_response}")
            raise FailedGettingAuthServiceResponseException()

        return None

    def _set_public_key_from_auth_service(self) -> None:
        """ Will query AUTH SERVICE for the public key used to validate JWT tokens issued by AUTH SERVICE.

        This method will set variables self._public_key + self._key_algorithm
        :raises FailedGettingAuthServiceResponseException: If fails to get 200 response from AUTH SERVICE
        :return: None
        """
        try:
            auth_service_response: Dict[str, any] = self._query_auth_service_api(
                method="GET",
                api_route=self.auth_service_get_public_key_api_route
            )
        except FailedGettingAuthServiceResponseException:
            logger.info("Failed getting public key from AUTH SERVICE API!")
            raise FailedGettingAuthServiceResponseException()

        try:
            self._public_key: str = auth_service_response["public_key"]
            self._key_algorithm: str = auth_service_response["key_format_algorithm"]
        except KeyError:
            logger.critical("Wrong JSON response from AUTH_SERVICE! "
                            "Missing one of the fields public_key or key_format_algorithm - "
                            f"returned response: {auth_service_response}")
            raise FailedGettingAuthServiceResponseException()

        return None

    def validate_token(self, jwt_token: str) -> Dict:
        """ Validates a token is authenticated and valid

        Checks two factors - 1) JWT signature is correct, 2) JWT expiration date is valid

        :param jwt_token:
        :raises JWTTokenInvalidException: In case JWT key is signed with wrong key or has expired
        :return: Dict, the JWT token payload
        """
        try:
            decoded_payload: Dict = jwt.decode(jwt=jwt_token, key=self._public_key, algorithms=[self._key_algorithm])
        except jwt.exceptions.DecodeError:
            logger.error("A JWT token with a bad signature! Someone tried to over-write the signature! ")
            raise JWTTokenInvalidException("Token is not signed correctly")
        except jwt.exceptions.ExpiredSignatureError:
            logger.info("A JWT which is expired was given, please refresh it")
            raise JWTTokenInvalidException("Token has expired")

        return decoded_payload
