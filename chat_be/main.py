from typing import Union, List, Dict
import uuid
from loguru import logger

from flask import Flask, make_response, Response, request, redirect, url_for
from flask_pydantic import validate as pydantic_validation

from sqlalchemy.orm import Session, scoped_session
from mysql_connector import models
from mysql_connector.database import SessionLocal, engine, sessionmaker
from mysql_connector import messages_table_crud_commands, users_table_crud_commands
from pydantic_schemas import messages_table_schemas, users_table_schemas, jwt_token_schemas, http_responses_schemas, \
    user_manager_service_responses_schemas
from init_objects import jwt_validator, auth_http_request, user_manager_integration
from utils.user_manager_integrations import FailedCreatingUserInUserManagerEmailAlreadyExistsException
from utils.auth_http_request import AuthorizationHeaderInvalidToken, AuthorizationHeaderJWTTokenNotPermitted
from flask_extensions.middleware import FlaskMiddleware
from flask_extensions.custom_decorators import user_jwt_token_required, request_json_data_required, \
    MissingAuthorizationHeader
from flask_extensions.custom_responses import custom_response_format
from flask_extensions.get_request_details import get_request_body, MissingRequestJSONDataField, \
    JSONDataFieldWrongValue, ContentTypeHeaderHasWrongValueException, ContentTypeHeaderNotExistException


""""
CHAT BACKEND service - handles users requests and manages messages DB
"""


# Dependency
def get_db():
    session = SessionLocal()
    return session


app = Flask(__name__)
app.wsgi_app = FlaskMiddleware(app.wsgi_app)



@app.route("/test", methods=["GET"])
@request_json_data_required(string_fields=["aaa"], int_fields=["aaaa"])
def user_login1(aaa, aaaa):
    logger.info("hello")
    return "hello!"


@app.route("/user/login", methods=["POST"])
def user_login():
    """ Logins the user

    :return:
    """
    resp: Response = make_response("1")
    resp.set_cookie('user_id', "aaaa")
    return resp


@app.route("/user/who_am_i", methods=["GET"])
@user_jwt_token_required
def user_who_am_i(user_details: jwt_token_schemas.JWTTokenRegisteredUser):
    """ Shows user's details according to JWT token + validating the JWT token

    Validation done by the decorator attached to this route

    # TODO - debug, maybe drop it in future
    :return:
    """
    return user_details.json()


@app.route("/user/create", methods=["POST"])
# @pydantic_validation()
def user_create(db: Session = get_db()):
    """ Will create a new user in the project. ( Will add the user in both USER MANAGER service DB and CHAT BE
    service DB )

    """
    try:
        new_user_details: user_manager_service_responses_schemas.UserManagerResponseUserDetailsBaseModule = \
            user_manager_integration.create_user(email="haxaasfdafsa",
                                                 password="aaaa",
                                                 db_session=db)
        logger.success(new_user_details)
        return "User created!"
    except FailedCreatingUserInUserManagerEmailAlreadyExistsException:
        return "Failed creating user - email already exists"


@app.route("/user/profile", methods=["GET"])
@user_jwt_token_required
def user_profile(user_id: int, db: Session = get_db()):
    """ Prints user's profile from database
    It can be assumed the user exist in the DB as the user introduced a valid JWT token issued by CHAT BE application
    """
    user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=user_id)
    return user_details


@app.route("/user/profile/edit", methods=["GET"])
@user_jwt_token_required
def user_profile_edit(db: Session = get_db()):
    """ Edit user's profile ( nickname + status )
    """
    user_updated_details = users_table_schemas.UserUpdateBaseModule(
        user_id=17,
        nickname="aaaa",
        text_status="aaaa",
    )
    try:
        updated_user_details: models.User = users_table_crud_commands.edit_user(
            db=db,
            user_details=user_updated_details
        )
        return updated_user_details.json()
    except users_table_crud_commands.UserNotFoundException:
        return "User ID not found"
    except users_table_crud_commands.UserFailedDatabaseUpdateException:
        return "Failed updating user in DB, try again"


@app.route("/users_details/", methods=["GET"])
# @pydantic_validation()
@user_jwt_token_required
def users_details(db: Session = get_db()):
    """ Prints a list of all existing users

    """
    users_list: List[models.User] = users_table_crud_commands.get_users_list(db=db, skip=0, limit=100)
    users_list_json: List[Dict] = [user.json() for user in users_list]
    return custom_response_format(status_code=200,
                                  content=users_list_json,
                                  text_message="Successfully got users details list")


@app.route("/users_details/<int:user_id>", methods=["GET"])
# @pydantic_validation()
@user_jwt_token_required
def user_details_id(user_id: int, db: Session = get_db()):
    """ Prints a list of all existing users

    """
    try:
        user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=user_id)
        return custom_response_format(status_code=200,
                                      content=user_details.json(),
                                      text_message="Successfully got user details")
    except users_table_crud_commands.UserNotFoundException:
        return custom_response_format(status_code=404,
                                      content=None,
                                      text_message="User not found with given ID",
                                      is_success=False)


@app.route("/admin/setup/database", methods=["GET"])
def setup_database():
    """ Setups the database by creating its tables
    This should be run only on first bootstrap of the application
    """
    models.Base.metadata.create_all(bind=engine)
    return {"message": "Finished creating tables"}


@app.route("/messages/send_message", methods=["POST"])
def messages_send_message():
    """ Allows a user to send a message to another user """
    return ""


@app.route("/messages/all_messages", methods=["GET"])
def messages_all_messages():
    """ Shows all messages sent to a user ever """
    return ""


@app.route("/messages/chat/<int:user_id>", methods=["GET"])
def messages_chat_history():
    """ Shows chat history of two users ( all messages sent and accepted between a user and another user ) """
    return


@app.route("/messages/message/<int:message_id>", methods=["DELETE"])
def messages_delete_message():
    """ Deletes a message sent by a user """
    return


@app.route("/messages/message/<int:message_id>", methods=["POST"])
def messages_update_message():
    """ Updates a message sent by a user """
    return


@app.errorhandler(AuthorizationHeaderInvalidToken)
def exception_handler(e):
    """ Raises when a wrong authorization header is sent from client. This will occur only in Flaks routes which use the
    decorator @user_jwt_token_required which will try to read the authorization header.

    Authorization header should be - "Authorization: Bearer <JWT token>"
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Wrong/Missing authorization header - "
                                               "should be \"Authorization: Bearer <JWT token>\"")


@app.errorhandler(AuthorizationHeaderInvalidToken)
def exception_handler(exception):
    """ Raises when a wrong authorization header is sent from client. This will occur only in Flaks routes which use the
    decorator @user_jwt_token_required which will try to read the authorization header.

    Authorization header should be - "Authorization: Bearer <JWT token>"
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Wrong authorization header value - "
                                               "should be \"Authorization: Bearer <JWT token>\"")


@app.errorhandler(AuthorizationHeaderJWTTokenNotPermitted)
def exception_handler_authorization_header_jwt_token_not_permitted(exception):
    """ Raises when a client sent a JWT token with not enough permissions to do an action.

    This will occur only in Flaks routes which use the decorator @user_jwt_token_required which will try to read the
    authorization header.

    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="JWT token lack permissions to do this action")


@app.errorhandler(MissingAuthorizationHeader)
def exception_handler_missing_authorization_header(exception):
    """ Raises when a client reqeust is missing a header named "Authorization" .

    In CHAT BE APP - any route which requires Authorization header should be - "Authorization: Bearer <JWT token>"
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing authorization header - following header should be attached "
                                               "to a request \"Authorization: Bearer <JWT token>\"")


@app.errorhandler(ContentTypeHeaderNotExistException)
def exception_handler_content_type_header_not_exist(exception):
    """ Raises when a client reqeust is missing a header named "Content-Type" . ( Required for JSON HTTP requests ) """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing Content-Type header - following header should be attached "
                                               "to a request \"Content-Type: application/json\"")


@app.errorhandler(ContentTypeHeaderHasWrongValueException)
def exception_handler_content_type_header_Has_(exception):
    """ Raises when a client reqeust has "Content-Type" header with value other than "application/json" . ( Required for
    JSON HTTP requests ) """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Wrong value for Content-Type header - "
                                               "should be \"Content-Type: application/json\"")


@app.errorhandler(MissingRequestJSONDataField)
def exception_handler_missing_request_json_data_field(exception):
    """ Raises when a client reqeust has JSON data with missing fields.

    Relates to decorator @request_json_data_required which read JSON data from HTTP requests sent by clients.
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing JSON data fields in the HTTP request!")


@app.errorhandler(JSONDataFieldWrongValue)
def exception_handler_json_data_field_wrong_value(exception):
    """ Raises when a client reqeust has JSON data with fields which have wrong type values. ( For example a filed which
    should have a string value is having an int value, and vice versa )

    Relates to decorator @request_json_data_required which read JSON data from HTTP requests sent by clients.
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing JSON data fields in the HTTP request!")
