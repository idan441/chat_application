from typing import Union, Tuple, Dict, Literal, Optional
import requests
from loguru import logger
from sqlalchemy.orm import Session

from .jwt_validator import AuthServiceJWTValidator
from pydantic_schemas import user_manager_service_responses_schemas, users_table_schemas
from mysql_connector import users_table_crud_commands


"""
Class for integrating with USER MANAGER service
"""


class FailedGettingUserManagerServiceResponseException(Exception):
    """ Raises when trying to query USER MANAGER service, and it is not available or returns a bad response."""

    def __init__(self, error_message: str = ""):
        """

        :param error_message: Optional - a custom message regarding why the exception raised
        """
        logger.error(f"Failed contacting USER MANAGER service returned error - {error_message}")
        super().__init__()


class FailedCreatingUserInUserManagerEmailAlreadyExistsException(Exception):
    """ Raises when trying to create a new user in UM service and the given email address is already in use. """
    pass


class UserNotExistInUserManagerException(Exception):
    """ Raises when trying to query for a user in UM service and no such user is found. """
    pass


class BasResponseFromUserManagerException(Exception):
    """ Raises when UM responds with a bad response which is not expected. ( Mainly 5XX codes )
    If this exception raises then it can be assumed that the HTTP request was rejected by the UM service. """

    def __init__(self, status_code: int, um_http_response: Union[str, Dict], error_message: str = ""):
        """

        :param status_code:
        :param um_http_response:
        :param error_message: Optional - a custom message regarding why the exception raised
        """
        self.status_code: int = status_code
        self.um_http_response: Union[str, Dict] = um_http_response
        logger.error("USER MANAGER returned a bad response - "
                     f"error '{error_message}' , status code {self.status_code} , content: {self.um_http_response}")
        super().__init__()


class UserManagerIntegration:
    """ Integrating with USER MANAGER (UM) service """

    def __init__(self,
                 jwt_validator: AuthServiceJWTValidator,
                 um_service_address: str,
                 um_service_get_user_details_route: str,
                 um_service_create_user_route: str,
                 um_service_login_user_route: str):
        """

        """
        self.jwt_validator = jwt_validator
        self.um_service_address: str = um_service_address
        self.um_service_get_user_details_route: str = um_service_get_user_details_route
        self.um_service_create_user_route: str = um_service_create_user_route
        self.um_service_login_user_route: str = um_service_login_user_route

    def _query_auth_service_api(self,
                                api_route: str,
                                method: Literal["GET", "POST"],
                                authorization_jwt: Optional[str] = None,
                                request_data: Optional[Dict] = None) -> Tuple[int, Dict[str, any]]:
        """ Queries UM service API, and returns the result as a dictionary.

        :param api_route:
        :param method: HTTP method to query UM service API
        :param authorization_jwt: Optional - JWT token used to authenticate with UM service ( JWT should be issued by
                                             AUTH SERVICE )
        :param request_data: Optional - JSON data to include in the HTTP request
        :raises FailedGettingUserManagerServiceResponseException: In case UM is not available, or its response fails to
                                                                  be read. ( Bad JSON format etc... )
        :return: A tuple - status code returned from UM service + a dictionary based on JSON response from UM service
        """
        endpoint_url: str = f"{self.um_service_address}{api_route}"
        headers: Dict = {"Content-Type": "application/json"}
        json_data: Dict = {}

        if authorization_jwt is not None:
            headers = {**headers, "Authorization": f"Bearer {authorization_jwt}"}
        if request_data is not None:
            json_data = {**json_data, **request_data}

        try:
            request = requests.request(
                method=method,
                url=endpoint_url,
                headers=headers,
                json=json_data,
            )
        except requests.exceptions.RequestException as e:
            raise FailedGettingUserManagerServiceResponseException("Failed getting answer from USER MANAGER service! "
                                                                   f"Returned error: {e}")

        status_code: int = request.status_code

        try:
            um_service_json_response: Dict[str, any] = request.json()
        except ValueError:
            logger.critical(f"Failed parsing the JSON response from USER MANAGER service! ")
            raise FailedGettingUserManagerServiceResponseException()

        logger.info(f"Successfully got response from UM service with status code {status_code} "
                    f"and JSON content: {um_service_json_response}")
        return status_code, um_service_json_response

    def get_user_details(self, user_id: int):
        """ Will get user details from UM service

        UM response for route GET /chat_be/user/{user_id} is -
        * 200 success - if user exists
        * 404 not found - if user doesn't exist with that ID
        """
        full_endpoint: str = f"{self.um_service_get_user_details_route}/{user_id}"
        status_code, um_service_response = self._query_auth_service_api(
            api_route=full_endpoint,
            method="GET",
            authorization_jwt=self.jwt_validator.get_microservice_jwt(),
        )
        if status_code == 200:
            pass
        elif status_code == 404:
            raise UserNotExistInUserManagerException(f"No user found in UM database with user ID {user_id}")
        else:
            raise BasResponseFromUserManagerException(error_message=f"Failed creating user - code {status_code} "
                                                                    f"reason: {um_service_response}")

    def create_user(self, email: str, password: str, db_session: Session) -> \
            user_manager_service_responses_schemas.UserManagerResponseUserDetailsBaseModule:
        """ Will create a user in UM service

        UM response for route POST /chat_be/users/create is -
        * 201 created - if user is created
        * 400 bad request - if email already exists

        :param email: email for the new user
        :param password: password for the new user ( Saved in UM DB, will not be saved in CHAT BE DB )
        :param db_session:
        :raise FailedCreatingUserInUserManagerEmailAlreadyExistsException: In case email address already exists in UM
        :raise BasResponseFromUserManagerException: In case UM returned an unknown response (mainly 5XX)
        :return:
        """
        full_endpoint: str = f"{self.um_service_create_user_route}"
        status_code, um_service_response = self._query_auth_service_api(
            api_route=full_endpoint,
            method="POST",
            request_data={
                "email": email,
                "password": password,
            },
            authorization_jwt=self.jwt_validator.get_microservice_jwt(),
        )

        if status_code == 201:
            created_user_details = user_manager_service_responses_schemas.UserManagerResponseUserDetailsBaseModule.\
                parse_obj(obj=um_service_response["content"])
            chat_be_db_user_details = users_table_schemas.UserCreateBaseModule(
                user_id=created_user_details.user_id,
                email=created_user_details.email
            )

            users_table_crud_commands.create_user(db=db_session, user=chat_be_db_user_details)
            logger.info(f"Successfully created new user with email address - {email}")
            return created_user_details
        elif status_code == 400:
            raise FailedCreatingUserInUserManagerEmailAlreadyExistsException("Failed creating user - "
                                                                             "email is already taken!")
        else:
            raise BasResponseFromUserManagerException(error_message=f"Failed creating user",
                                                      status_code=status_code,
                                                      um_http_response=um_service_response)

    def login_user(self, email: str, password: str, db_session: Session) -> \
            user_manager_service_responses_schemas.UserManagerUserLoginResponseBaseModule:
        """ Will check if user login details are correct in-front of UM microservice.
        Two things should be checked: 1) username and password are correct 2) user is-active ( un-activated users aren't
        allowed to use the application )

        :param email:
        :param password:
        :param db_session:
        :raise BasResponseFromUserManagerException: In case UM returned an unknown response (mainly 5XX)
        :return: Login attempt details
        """
        full_endpoint: str = f"{self.um_service_login_user_route}"
        status_code, um_service_response = self._query_auth_service_api(
            api_route=full_endpoint,
            method="POST",
            request_data={
                "email": email,
                "password": password,
            },
            authorization_jwt=self.jwt_validator.get_microservice_jwt(),
        )

        user_login_attempt_details = user_manager_service_responses_schemas.UserManagerUserLoginResponseBaseModule. \
            parse_obj(obj=um_service_response["content"])
        logger.info(f"Login attempt for user {email} - UM returned: {user_login_attempt_details}")
        return user_login_attempt_details
