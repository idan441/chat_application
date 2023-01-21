from fastapi import Header, HTTPException, status as HTTP_STATUS_CODES

from init_objects import auth_http_request
from fast_api_extensions.auth_http_request import AuthorizationHeaderJWTTokenNotPermitted, \
    AuthorizationHeaderInvalidHeaderFormat, AuthorizationHeaderInvalidToken
from constants import MicroServicesNames


"""
Includes methods used for creating FastAPI routes dependencies. These will be used to enforce specific values are passed
in every HTTP request sent to it.
"""


def require_microservice_jwt_token(authorization_bearer_header: str = Header("Authorization")):
    try:
        microservice_token = auth_http_request.verify_micro_service_jwt_token(
            authorization_bearer_header=authorization_bearer_header
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


def require_chat_be_microservice_jwt_token(authorization_bearer_header: str = Header("Authorization")):
    try:
        microservice_token = auth_http_request.verify_micro_service_jwt_token(
            authorization_bearer_header=authorization_bearer_header,
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


def require_registered_user_jwt_token(authorization_bearer_header: str = Header("Authorization")):
    try:
        microservice_token = auth_http_request.verify_registered_user_jwt_token(
            authorization_bearer_header=authorization_bearer_header
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
