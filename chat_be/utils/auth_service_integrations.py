from typing import Union, Tuple, Dict, Literal, Optional
import requests
from loguru import logger

from .jwt_validator import AuthServiceJWTValidator


"""
Class for integrating with authentication service (AUTH SERVICE)
"""


class FailedGettingAuthServiceResponseException(Exception):
    """ Raises when trying to query AUTH service, and it is not available or returns a bad response."""

    def __init__(self, error_message: str = ""):
        """

        :param error_message: Optional - a custom message regarding why the exception raised
        """
        logger.error(f"Failed contacting AUTH service returned error - {error_message}")
        super().__init__()


class BasResponseFromAuthServiceException(Exception):
    """ Raises when AUTH service responds with a bad response which is not expected. ( Mainly 5XX codes )
    If this exception raises then it can be assumed that the HTTP request was rejected by the AUTH service. """

    def __init__(self, status_code: int, auth_service_http_response: Union[str, Dict], error_message: str = ""):
        """

        :param status_code:
        :param auth_service_http_response:
        :param error_message: Optional - a custom message regarding why the exception raised
        """
        self.status_code: int = status_code
        self.auth_service_http_response: Union[str, Dict] = auth_service_http_response
        logger.error("USER MANAGER returned a bad response - "
                     f"error '{error_message}' , status code {self.status_code} , "
                     f"content: {self.auth_service_http_response}")
        super().__init__()


class AuthServiceIntegration:
    """ Integrating with AUTH SERVICE """

    def __init__(self,
                 jwt_validator: AuthServiceJWTValidator,
                 auth_service_address: str,
                 auth_service_issue_user_jwt_token_route: str):
        """

        """
        self.jwt_validator = jwt_validator
        self.auth_service_address: str = auth_service_address
        self.auth_service_issue_user_jwt_token_route: str = auth_service_issue_user_jwt_token_route

    def _query_auth_service_api(self,
                                api_route: str,
                                method: Literal["GET", "POST"],
                                authorization_jwt: Optional[str] = None,
                                request_data: Optional[Dict] = None) -> Tuple[int, Dict[str, any]]:
        """ Queries AUTH service API, and returns the result as a dictionary.

        :param api_route:
        :param method: HTTP method to query AUTH service API
        :param authorization_jwt: Optional - JWT token used to authenticate with AUTH service ( JWT is issued by
                                             AUTH SERVICE at first )
        :param request_data: Optional - JSON data to include in the HTTP request
        :raises FailedGettingAuthServiceResponseException: In case AUTH service is not available, or its response fails
                                                           to be read. ( Bad JSON format etc... )
        :return: A tuple - status code + a dictionary based on JSON response from AUTH service
        """
        endpoint_url: str = f"{self.auth_service_address}{api_route}"
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
            raise FailedGettingAuthServiceResponseException("Failed getting answer from AUTH service! "
                                                            f"Returned error: {e}")

        status_code: int = request.status_code

        try:
            auth_service_json_response: Dict[str, any] = request.json()
        except ValueError:
            logger.critical(f"Failed parsing the JSON response from AUTH service! ")
            raise FailedGettingAuthServiceResponseException()

        logger.info(f"Successfully got response from AUTH service with status code {status_code}")
        return status_code, auth_service_json_response

    def issue_user_jwt_token(self, user_id: int, email: str, is_active: bool) -> str:
        """ Will request AUTH service to issue a user JWT token

        AUTH response for route POST /issue_user_jwt is -
        * 201 created - with JWT token attached

        :param user_id:
        :param email: email for the new user
        :param is_active
        :raise FailedGettingAuthServiceResponseException: in case AUTH service is not available or its response is not
                                                          JSON parse-able
        :raise BasResponseFromAuthServiceException: In case AUTH returned an unknown response (mainly 5XX)
        :return:
        """
        full_endpoint: str = f"{self.auth_service_issue_user_jwt_token_route}"
        status_code, auth_service_response = self._query_auth_service_api(
            api_route=full_endpoint,
            method="POST",
            request_data={
                "user_id": user_id,
                "email": email,
                "is_active": is_active,
            },
            authorization_jwt=self.jwt_validator.get_microservice_jwt(),
        )

        if status_code == 201:
            user_jwt_token = auth_service_response["jwt_token"]  # TODO - improve AUTH service response to include "content" field which will include jwt_token

            logger.info(f"Successfully issued a user JWT token for user ID {user_id} email {email}")
            return user_jwt_token
        else:
            raise BasResponseFromAuthServiceException(error_message=f"Failed issuing a user JWT token",
                                                      status_code=status_code,
                                                      auth_service_http_response=auth_service_response)
