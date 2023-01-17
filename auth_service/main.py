import os
from typing import Dict
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status as HTTP_STATUS_CODES
from loguru import logger

import http_responses_schemas
from jwt_utils import JWTHelper, JWTTokenInvalidException


def configure_custom_logger(logs_file_path: str) -> None:
    """ Will configure the logging module to use a JSON customized logging

    :param logs_file_path:
    :return: None
    """
    logger.remove(0)
    logger.add(logs_file_path,
               format="{time} | {level} | {extra[request_uuid]} | Message : {message}",
               colorize=False,
               serialize=True)

    return None


load_dotenv()
jwt_helper = JWTHelper(private_key=os.environ["JWT_PRIVATE_KEY"],
                       public_key=os.environ["JWT_PUBLIC_KEY"],
                       key_algorithm=os.environ["KEY_ALGORITHM"],
                       expiration_time_in_hours=int(os.environ["JWT_VALIDITY_IN_HOURS"]))
configure_custom_logger(logs_file_path=os.environ["LOGS_FILE_PATH"])

app = FastAPI()


@app.middleware("http")
async def http_middleware(request: Request, call_next):
    """ Sets a middleware for the FastAPI server. Also adds a contextualized logging level """
    with logger.contextualize(request_uuid=uuid.uuid4()):
        logger.info(request.base_url)
        response: Response = await call_next(request)
        logger.info(f"status_code: {response.status_code}")
    return response


@app.get("/get_public_key",
         status_code=HTTP_STATUS_CODES.HTTP_200_OK,
         response_model=http_responses_schemas.HTTPTemplateBaseModelPublicKey)
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is know to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    public_key, key_format_algorithm = jwt_helper.get_public_key(), jwt_helper.get_key_algorithm()
    return http_responses_schemas.HTTPTemplateBaseModelPublicKey(
        public_key=public_key,
        key_format_algorithm=key_format_algorithm,
        text_message="Successfully returned public key"
    )


@app.post("/sign_service_jwt",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=http_responses_schemas.HTTPTemplateBaseModelJWTToken)
def sign_service_jwt():
    """ Signs a JWT token which will be used to authenticate between microservices in this project """
    service_token_payload: Dict[str, any] = {
        "service_name": "auth_service",
    }
    jwt_token: str = jwt_helper.sign_token(payload=service_token_payload)
    return http_responses_schemas.HTTPTemplateBaseModelJWTToken(
        jwt_token=jwt_token,
        text_message="Successfully returned a micro-service JWT token"
    )


@app.post("/sign_user_jwt",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=http_responses_schemas.HTTPTemplateBaseModelJWTToken)
def sign_user_jwt():
    """ Signs a JWT token which will be used by users to authenticate with other microservices in this project """
    user_token_payload: Dict[str, any] = {
        "user_id": 1,
        "email": "aa",
    }
    jwt_token: str = jwt_helper.sign_token(payload=user_token_payload)
    return http_responses_schemas.HTTPTemplateBaseModelJWTToken(
        jwt_token=jwt_token,
        text_message="Successfully returned a user JWT token"
    )


@app.post("/validate_jwt_token",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=http_responses_schemas.HTTPTemplateBaseModelJWTTokenValidation)
def validate_jwt_token(response: Response):
    """ Signs a JWT token which will be used by users to authenticate with other microservices in this project """
    jwt_token: str = "test"
    try:
        jwt_helper.validate_token(jwt_token=jwt_token)
        return http_responses_schemas.HTTPTemplateBaseModelJWTTokenValidation(
            is_jwt_valid=True,
            text_message="JWT token is valid"
        )
    except JWTTokenInvalidException:
        response.status_code = HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED
        return http_responses_schemas.HTTPTemplateBaseModelJWTTokenValidation(
            is_jwt_valid=False,
            text_message="JWT token is invalid"
        )

