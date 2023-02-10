from time import sleep
from typing import Dict, Optional, Literal, Tuple, Union
from datetime import datetime, timedelta
import requests
import jwt
from loguru import logger

from pydantic_schemas.jwt_token_schemas import JWTTokenMicroService, JWTTokenRegisteredUser
from constants import JWTTypes


"""
Defines a class which can validate JWT tokens issued by the AUTH SERVICE
Public key which is needed to validate the JWT tokens will be read from AUTH SERVICE
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


class JWTInvalidAuthException(Exception):
    """ Raises when a given JWT token is invalid.
     This exception is used when a microservice tries to authenticate with auth service and uses an invalid token.
     ( And not when a microservice tries to issue a JWT token ) """
    pass


class FailedParsingJWTToken(Exception):
    """ Raises when fails to read a JWT token. This should be used after verifying the JWT token is authenticated so it
    will raise if the JWT token is missing fields. ( "email", "is_active" etc... ) """
    pass


class AuthServiceJWTValidator:
    """ Validates JWT tokens issued by AUTH SERVICE
    JWT tokens should follow the format used in the project. """

    def __init__(self,
                 auth_service_address: str,
                 auth_service_get_public_key_api_route: str,
                 auth_service_issue_microservice_jwt_token_api_route: str,
                 micro_service_initial_token: str,
                 micro_service_name: str):
        """

        :param auth_service_address:
        :param auth_service_get_public_key_api_route:
        :param auth_service_issue_microservice_jwt_token_api_route:
        :param micro_service_initial_token:
        :param micro_service_name:
        """
        # AUTH SERVICE endpoints addresses
        self.auth_service_address: str = auth_service_address
        self.auth_service_get_public_key_api_route: str = auth_service_get_public_key_api_route
        self.auth_service_issue_microservice_jwt_token_api_route: str = \
            auth_service_issue_microservice_jwt_token_api_route

        # Used to authenticate in front of AUTH SERVICE (token is a shared secret with AUTH SERVICE)
        self.micro_service_initial_token: str = micro_service_initial_token
        self.micro_service_name: str = micro_service_name

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
        """ Will return the microservice JWT token, so it can be used by application to contact other microservices in
        the project.

        If microservice JWT token has expired, it will auto-renew it.

        :return: JWT token
        """
        # JWT token must be valid when read by other services, so it should be considered expired a minute before
        jwt_real_expire_time: datetime = datetime.utcnow() - timedelta(minutes=1)
        if self._microservice_jwt_token_expire_datetime < jwt_real_expire_time:
            self._get_microservice_jwt_token_from_auth_service()
        return self._microservice_jwt_token

    def _query_auth_service_api(self,
                                api_route: str,
                                method: Literal["GET", "POST"],
                                authorization_jwt: Optional[str] = None,
                                request_data: Optional[Dict] = None) -> Dict[str, any]:
        """ Queries AUTH SERVICE API, and returns the result as a dictionary.

        :param api_route:
        :param method: HTTP method to query AUTH SERVICE API
        :param authorization_jwt: Optional - JWT token used to authenticate with AUTH SERVICE
        :param request_data: Optional - JSON data to include in the HTTP request
        :raises FailedGettingAuthServiceResponseException: In case AUTH SERVICE is not available, or the returned
                                                           response is not 200 or JSON valid
        :return: dictionary based on JSON response from AUTH SERVICE
        """
        get_public_key_endpoint: str = f"{self.auth_service_address}{api_route}"
        headers: Dict = {"Content-Type": "application/json"}
        json_data: Dict = {}

        if authorization_jwt is not None:
            headers = {**headers, "Authorization": f"Bearer {authorization_jwt}"}
        if request_data is not None:
            json_data = {**json_data, **request_data}

        try:
            request = requests.request(
                method=method,
                url=get_public_key_endpoint,
                headers=headers,
                json=json_data,
             )
        except requests.exceptions.RequestException as e:
            logger.critical(f"Failed getting answer from AUTH SERVICE! Returned error: {e}")
            raise FailedGettingAuthServiceResponseException()

        status_code: int = request.status_code
        if not 200 <= status_code <= 299:
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
                api_route=self.auth_service_issue_microservice_jwt_token_api_route,
                request_data={
                    "micro_service_name": self.micro_service_name,
                    "micro_service_initial_token": self.micro_service_initial_token,
                }
            )
        except FailedGettingAuthServiceResponseException:
            logger.info("Failed getting microservice JWT token from AUTH SERVICE API!")
            raise FailedGettingAuthServiceResponseException()

        try:
            self._microservice_jwt_token: str = auth_service_response["jwt_token"]

            jwt_token_expire_unix_time: int = self._validate_token(jwt_token=self._microservice_jwt_token)["exp"]
            self._microservice_jwt_token_expire_datetime = datetime.utcfromtimestamp(jwt_token_expire_unix_time)
        except KeyError:
            logger.critical("Wrong JSON response from AUTH_SERVICE!"
                            f"Missing field microservice_jwt_token - returned response: {auth_service_response}")
            raise FailedGettingAuthServiceResponseException()

        logger.success(f"Got a microservice JWT token from AUTH SERVICE! "
                       f"JWT token will expire at: {self._microservice_jwt_token_expire_datetime} UTC")
        return None

    def _set_public_key_from_auth_service(self) -> None:
        """ Will query AUTH SERVICE for the public key used to validate JWT tokens issued by AUTH SERVICE.

        This method will set variables self._public_key + self._key_algorithm

        This method requires self._microservice_jwt_token to be assigned first, as AUTH SERVICE API requires a JWT token
        in order to query for the public key.

        :raises FailedGettingAuthServiceResponseException: If fails to get 200 response from AUTH SERVICE
        :return: None
        """
        try:
            auth_service_response: Dict[str, any] = self._query_auth_service_api(
                api_route=self.auth_service_get_public_key_api_route,
                method="GET",
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

        logger.success("Got public key details from AUTH SERVICE!")
        return None

    def _validate_token(self, jwt_token: str) -> Dict:
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
        except jwt.exceptions.InvalidAlgorithmError:
            logger.info("Failed authenticating JWT because algorithm used for deciphering is wrong! The key algorithm "
                        f"is: {self._key_algorithm}")
            raise JWTTokenInvalidException("Failed deciphering JWT token with current key algorithm: Check algorithm "
                                           "is correct or maybe JWT is badly signed")

        return decoded_payload

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
        """ Read a JWT token issued by the auth service and returns its payload as an object representing it. ( Custom
        class which assures JWT token contains all fields needed )

        :param jwt_token:
        :raises JWTTokenInvalidException: In case token is not valid (bad signature or token expired)
        :raises FailedParsingJWTToken: In case token is valid, but its payload is missing fields ( This is not supposed
                                       to happen and probably means the private key was stolen to fake the JWT )
        :return: Tuple - token type (microservice or registered user) and an object representing the token payload
        """
        try:
            token_payload: Dict[str, any] = self._validate_token(jwt_token=jwt_token)
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
