import os
from typing import Dict
from dotenv import load_dotenv
from loguru import logger

from logger.custom_logger import configure_custom_logger
from utils.jwt_issuer import JWTIssuer
from utils.microservices_token_mapping_helper import MicroservicesTokenMappingHelper
from fast_api_extensions.auth_http_request import AuthHTTPRequest
from constants import MicroservicesTokenMapping

"""
Will create some objects which are needed to run the AUTH SERVICE application
Reason for using this file and not main.py is because it needs to be imported by other modules too.
"""


with logger.contextualize(request_uuid="init"):
    logger.info("Initializing objects used by application to run")

    load_dotenv()
    logger.success("Read ENV VARs successfully")

    logger.info("Configuring custom logger")
    configure_custom_logger(logs_file_path=os.environ["LOGS_FILE_PATH"])

    logger.info("Reading microservices shared tokens ENV VARs")
    microservices_token_helper = MicroservicesTokenMappingHelper(
        microservice_tokens_env_vars_dict=MicroservicesTokenMapping.MICROSERVICES_TOKENS_ENV_VARS_DICT
    )
    microservices_token_helper.read_token_from_env_vars()
    microservices_tokens_mapping: Dict[str, str] = microservices_token_helper.microservices_mapping_dict
    logger.info("Finished reading microservices shared tokens ENV VARs")

    logger.info("Creating JWTIssuer object to issue JWT tokens")
    jwt_issuer = JWTIssuer(private_key=os.environ["JWT_PRIVATE_KEY"],
                           public_key=os.environ["JWT_PUBLIC_KEY"],
                           key_algorithm=os.environ["KEY_ALGORITHM"],
                           expiration_time_in_hours=int(os.environ["JWT_VALIDITY_IN_HOURS"]),
                           microservices_tokens_mapping=microservices_tokens_mapping)

    logger.info("Creating AuthHTTPRequest used to authenticate client requests in front of application")
    auth_http_request = AuthHTTPRequest(jwt_issuer=jwt_issuer)

    logger.success("Finished initializing objects! Preparing to launch application")
