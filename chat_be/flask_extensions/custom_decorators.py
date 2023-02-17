from flask import request
from init_objects import auth_http_request
from pydantic_schemas.jwt_token_schemas import JWTTokenRegisteredUser
from utils.auth_http_request import AuthorizationHeaderInvalidToken, AuthorizationHeaderJWTTokenNotPermitted
from functools import wraps


"""
Custom decorators used to enrich Flask functionality
"""


def user_jwt_token_required(f):
    """ Makes sure the HTTP request needs a user-type JWT token

    * Will validate the HTTP request sent by client includes a JWT token
    * will verify the JWT token is of type "registered_user"
    * will inject the following two arguments to the Flask route function -
      * user_id: int - only the user id
      * user_details: JWTTokenRegisteredUser - contains all user's details from the JWT token

    In case JWT is invalid an exception will be raised. There is a Flask error handler for these exception which will
    return a custom response to the client.

    :raises AuthorizationHeaderInvalidToken: If authorization header is wrong or not given
    :raises AuthorizationHeaderJWTTokenNotPermitted: If JWT token is invalid or not permitted
    :return: Flask route response
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            authorization_header: str = request.headers["Authorization"]
        except KeyError:
            raise AuthorizationHeaderInvalidToken("Missing Authorization header")

        user_details: JWTTokenRegisteredUser = auth_http_request.verify_registered_user_jwt_token(
            authorization_bearer_header=authorization_header
        )
        user_id: int = user_details.user_id
        return f(user_id, user_details, *args, **kwargs)

    return decorated_function
