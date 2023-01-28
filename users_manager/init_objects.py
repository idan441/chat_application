import os
from dotenv import load_dotenv
from loguru import logger

from logger.custom_logger import configure_custom_logger
from utils.jwt_validator import AuthServiceJWTValidator
from fast_api_extensions.auth_http_request import AuthHTTPRequest
from constants import MicroServicesNames


"""
Will create some objects which are needed to run the AUTH SERVICE application
Reason for using this file and not main.py is because it needs to be imported by other modules too.
"""


with logger.contextualize(request_uuid="init"):
    load_dotenv()
    configure_custom_logger(logs_file_path=os.environ["LOGS_FILE_PATH"])

    jwt_validator = AuthServiceJWTValidator(
        auth_service_address=os.environ["AUTH_SERVICE_ADDRESS"],
        auth_service_get_public_key_api_route=os.environ["AUTH_SERVICE_GET_PUBLIC_KEY_API_ROUTE"],
        auth_service_issue_microservice_jwt_token_api_route=
        os.environ["AUTH_SERVICE_ISSUE_MICROSERVICE_JWT_TOKEN_API_ROUTE"],
        micro_service_name=MicroServicesNames.USERS_MANAGER,
        micro_service_initial_token=os.environ["AUTH_SERVICE_USER_MANAGER_SHARED_SECRET"],
    )
    jwt_validator.initial_jwt_validator()
    auth_http_request = AuthHTTPRequest(jwt_validator=jwt_validator)
