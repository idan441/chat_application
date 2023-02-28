from typing import Union
import uuid
from fastapi import FastAPI, Request, Response, Depends, status as HTTP_STATUS_CODES
from loguru import logger

from pydantic_schemas import http_responses_schemas, request_input_schemas
from utils.jwt_issuer import MicroserviceAuthenticationTokenInvalidException
from init_objects import jwt_issuer
from fast_api_extensions.fast_api_dependencies import require_microservice_jwt_token, \
    require_chat_be_microservice_jwt_token


"""
Authentication service (auth service)
Used to issue and manage JWT token for all microservices and users who authenticate the project 
"""


app = FastAPI()


@app.middleware("http")
async def http_middleware(request: Request, call_next):
    """ Sets a middleware for the FastAPI server. Also adds a contextualized logging level """
    with logger.contextualize(request_uuid=uuid.uuid4()):
        response: Response = await call_next(request)
        logger.info(f"status_code: {response.status_code}")
    return response


@app.get("/get_public_key",
         status_code=HTTP_STATUS_CODES.HTTP_200_OK,
         response_model=http_responses_schemas.HTTPTemplateBaseModelPublicKey,
         )
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    public_key, key_format_algorithm = jwt_issuer.get_public_key(), jwt_issuer.get_key_algorithm()
    return http_responses_schemas.HTTPTemplateBaseModelPublicKey(
        public_key=public_key,
        key_format_algorithm=key_format_algorithm,
        text_message="Successfully returned public key"
    )


@app.post("/validate_jwt_token",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=http_responses_schemas.HTTPTemplateBaseModelJWTTokenValidation)
def validate_jwt_token(jwt_token_details: request_input_schemas.HTTPRequestValidateJWTTokenModel, response: Response):
    """ Validate if a given JWT token was issued by the auth service.
        If token has expired - it will be considered not validated, even if it was issued by auth service. """
    jwt_token: str = jwt_token_details.jwt_token
    if jwt_issuer.is_token_valid(jwt_token=jwt_token):
        return http_responses_schemas.HTTPTemplateBaseModelJWTTokenValidation(
            is_jwt_valid=True,
            text_message="JWT token is valid"
        )
    else:
        response.status_code = HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED
        return http_responses_schemas.HTTPTemplateBaseModelJWTTokenValidation(
            is_jwt_valid=False,
            text_message="JWT token is invalid"
        )


@app.post("/issue_service_jwt",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=Union[http_responses_schemas.HTTPTemplateBaseModelJWTToken,
                               http_responses_schemas.HTTPTemplateBaseModelJWTTokenIssueFailedValidation])
def issue_service_jwt(service_auth_details: request_input_schemas.HTTPRequestIssueServiceJWTModel,
                      response: Response):
    """ Signs a JWT token which will be used to authenticate between microservices in this project """
    try:
        jwt_token: str = jwt_issuer.issue_micro_service_jwt(service_auth_details=service_auth_details)
        return http_responses_schemas.HTTPTemplateBaseModelJWTToken(
            jwt_token=jwt_token,
            text_message="Successfully returned a micro-service JWT token"
        )
    except MicroserviceAuthenticationTokenInvalidException:
        response.status_code = HTTP_STATUS_CODES.HTTP_400_BAD_REQUEST
        return http_responses_schemas.HTTPTemplateBaseModelJWTTokenIssueFailedValidation(
            given_authentication_details=service_auth_details,
            is_success=False,
            text_message="Wrong token given, no micro-service JWT token issued"
        )


@app.post("/issue_user_jwt",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=http_responses_schemas.HTTPTemplateBaseModelJWTToken)
def issue_user_jwt(user_details: request_input_schemas.HTTPRequestIssueUserJWTModel,
                   microservice_token: str = Depends(require_chat_be_microservice_jwt_token)):
    """ Signs a JWT token which will be used by users to authenticate with other microservices in this project

    * This API route assumes the request is sent by a microservice which already authenticated the user.
    * This API route can be used only with a JWT token of CHAT BE microservice, which is the only microservice in the
      project which should authenticate users.
    """
    jwt_token: str = jwt_issuer.issue_user_jwt(user_details=user_details)
    return http_responses_schemas.HTTPTemplateBaseModelJWTToken(
        jwt_token=jwt_token,
        text_message="Successfully returned a user JWT token"
    )
