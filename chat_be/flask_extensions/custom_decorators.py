from typing import List
from functools import wraps, update_wrapper

from init_objects import auth_http_request
from pydantic_schemas.jwt_token_schemas import JWTTokenRegisteredUser
from flask_extensions.get_request_details import get_header_value_from_request, get_request_body, \
    HeaderNotExistException


"""
Custom decorators used to enrich Flask functionality
"""


class MissingAuthorizationHeader(Exception):
    """ Raises in case an "Authorization" header field doesn't exist but supposed to be sent by the client
    Example: trying to read an "Authorization" header from a request and the header doesn't exist. """
    pass


def user_jwt_token_required(f):
    """ Makes sure the HTTP request needs a user-type JWT token

    * Will validate the HTTP request sent by client includes a JWT token
    * will verify the JWT token is of type "registered_user"
    * will inject the following two arguments to the Flask route function -
      * user_id: int - only the user id
      * user_details: JWTTokenRegisteredUser - contains all user's details from the JWT token

    In case JWT is invalid or authorization header is missing or wrong - an exception will be raised. There is a Flask
    error handler for these exception which will return a custom response to the client.

    :raises AuthorizationHeaderNotExistException: In case no authorization header is sent in the request
    :raises AuthorizationHeaderInvalidToken: If authorization header is wrong or expired
    :raises AuthorizationHeaderJWTTokenNotPermitted: If JWT token is invalid or not permitted
    :return: Flask route response + injects a variables "user_id" and "user_details"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            authorization_header: str = get_header_value_from_request(header_name="Authorization")
        except HeaderNotExistException:
            raise MissingAuthorizationHeader("Missing \"Authorization\" header")

        user_details: JWTTokenRegisteredUser = auth_http_request.verify_registered_user_jwt_token(
            authorization_bearer_header=authorization_header
        )
        user_id: int = user_details.user_id
        return f(user_id, user_details, *args, **kwargs)

    return decorated_function


def request_json_data_required(string_fields: List[str] = None, int_fields: List[str] = None):
    """ Reads JSON data attached to HTTP requests sent by client and passes it to the method related to the Flask route.
    This will validate the fields exist and their value (str/int) - and will pass them forward as method arguments

    :param string_fields: field names  to read from JSON data request and have a string value
    :param int_fields: field names  to read from JSON data request and have an int value
    :raises ContentTypeHeaderNotExistException: In case header "Content-Type" is missing
    :raises ContentTypeHeaderHasWrongValueException: In case "Content-Type" is not "application/json"
    :raises ContentTypeHeaderHasWrongValueException: If "Content-Type" header is not "application/json"
    :raises ContentTypeHeaderNotExistException: If missing "Content-Type" header
    :return: Flask route response
    """
    def decorated_function(func):
        def wrapper(*args, **kwargs):
            variables_to_pass = get_request_body(string_fields=string_fields, int_fields=int_fields)
            return func(*args, **variables_to_pass, **kwargs)
        return update_wrapper(wrapper, func)
    return decorated_function
