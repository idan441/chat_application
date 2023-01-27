from fastapi import Header, HTTPException, status as HTTP_STATUS_CODES

from init_objects import auth_http_request
from fast_api_extensions.auth_http_request import AuthorizationHeaderJWTTokenNotPermitted, \
    AuthorizationHeaderInvalidHeaderFormat, AuthorizationHeaderInvalidToken
from constants import MicroServicesNames


"""
Includes methods used for creating FastAPI routes dependencies. These will be used to enforce specific values are passed
in every HTTP request sent to it.
"""


def require_microservice_jwt_token(Authorization: str = Header()):
    """ Verifies a microservice JWT token issued by AUTH SERVICE is attached to the HTTP request sent by client.
    JWT token should be attached as a header - "Authorization: Bearer <jwt token>"

    :return:
    """
    try:
        microservice_token = auth_http_request.verify_micro_service_jwt_token(
            authorization_bearer_header=Authorization
        )
        return microservice_token
    except AuthorizationHeaderJWTTokenNotPermitted:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="Not permitted to use this API route")
    except AuthorizationHeaderInvalidHeaderFormat:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="Authorization header content is invalid")
    except AuthorizationHeaderInvalidToken:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="JWT given is invalid")


def require_chat_be_microservice_jwt_token(Authorization: str = Header()):
    """ Verifies HTTP request is sent by CHAT BE microservice. This  is done by verifying attached JWT token is -
    1. Issued by AUTH SERVICE and is valid.
    2. Has the JWT token attached as HTTP header sent by client.
    3. JWT content contains field named "token_type" with value "microservice" .
    4. JWT content field named "service_name" with value "chat_be" (Unique value for CHAT BACKEND microservice)
    JWT token should be attached as a header - "Authorization: Bearer <jwt token>"

    :return:
    """
    try:
        microservice_token = auth_http_request.verify_micro_service_jwt_token(
            authorization_bearer_header=Authorization,
            micro_service_name=MicroServicesNames.CHAT_BE,
        )
        return microservice_token
    except AuthorizationHeaderJWTTokenNotPermitted:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="Not permitted to use this API route")
    except AuthorizationHeaderInvalidHeaderFormat:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="Authorization header content is invalid")
    except AuthorizationHeaderInvalidToken:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="JWT given is invalid")


def require_registered_user_jwt_token(Authorization: str = Header()):
    """ Verifies HTTP request is sent by CHAT BE microservice. This  is done by verifying attached JWT token is -
    1. Issued by AUTH SERVICE and is valid.
    2. Has the JWT token attached as HTTP header sent by client.
    3. JWT content contains field named "token_type" with value "registered_user" .

    JWT token should be attached as a header - "Authorization: Bearer <jwt token>"

    :return:
    """
    try:
        microservice_token = auth_http_request.verify_registered_user_jwt_token(
            authorization_bearer_header=Authorization
        )
        return microservice_token
    except AuthorizationHeaderJWTTokenNotPermitted:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="Not permitted to use this API route")
    except AuthorizationHeaderInvalidHeaderFormat:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="Authorization header content is invalid")
    except AuthorizationHeaderInvalidToken:
        raise HTTPException(status_code=HTTP_STATUS_CODES.HTTP_401_UNAUTHORIZED,
                            detail="JWT given is invalid")