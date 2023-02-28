from typing import List, Dict

from flask import Flask

from sqlalchemy.orm import Session, scoped_session
from mysql_connector import models
from mysql_connector.database import SessionLocal, engine, sessionmaker
from mysql_connector import messages_table_crud_commands, users_table_crud_commands
from pydantic_schemas import messages_table_schemas, users_table_schemas, jwt_token_schemas, http_responses_schemas, \
    user_manager_service_responses_schemas
from init_objects import user_manager_integration, auth_service_integration
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


@app.route("/user/login", methods=["POST"])
@request_json_data_required(string_fields=["email", "password"])
def user_login(email: str, password: str):
    """ Logins the user

    This route will contact USER MANAGER SERVICE and will verify the user details. If login details are correct and the
    user is active - then CHAT BE service will contact AUTH SERVICE for a use JWT token and will return it to the user.

    :return:
    """
    user_login_attempt_details: user_manager_service_responses_schemas.UserManagerUserLoginResponseBaseModule = \
        user_manager_integration.login_user(email=email,
                                            password=password)
    if user_login_attempt_details.is_login_success:
        if user_login_attempt_details.is_active:
            user_details = user_login_attempt_details.user_details
            jwt_token: str = auth_service_integration.issue_user_jwt_token(user_details=user_details)
            return custom_response_format(status_code=200,
                                          content=http_responses_schemas.HTTPResponseUserLogin(
                                              jwt_token=jwt_token,
                                              user_details=user_details,
                                          ),
                                          text_message="Successfully logged in")
        else:
            return custom_response_format(status_code=403,
                                          is_success=False,
                                          text_message="User is not active")
    else:
        return custom_response_format(status_code=400,
                                      is_success=False,
                                      text_message="Wrong email or password")


@app.route("/user/create", methods=["POST"])
@request_json_data_required(string_fields=["email", "password"])
def user_create(email: str, password: str, db: Session = get_db()):
    """ Will create a new user in the project. ( Will add the user in both USER MANAGER service DB and CHAT BE
    service DB )

    """
    try:
        new_user_details: user_manager_service_responses_schemas.UserManagerResponseUserDetailsBaseModule = \
            user_manager_integration.create_user(email=email,
                                                 password=password,
                                                 db_session=db)
        return custom_response_format(status_code=201,
                                      content=new_user_details,
                                      text_message="Successfully created new user")
    except FailedCreatingUserInUserManagerEmailAlreadyExistsException:
        return custom_response_format(status_code=409,
                                      is_success=False,
                                      text_message="Failed creating new user - email already in use")


@app.route("/user/profile", methods=["GET"])
@user_jwt_token_required
def user_profile(user_details: jwt_token_schemas.JWTTokenRegisteredUser, db: Session = get_db()):
    """ Prints user's profile from database
    It can be assumed the user exist in the DB as the user introduced a valid JWT token issued by CHAT BE application
    """
    created_user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=user_details.user_id)
    return custom_response_format(status_code=201,
                                  content=created_user_details.json(),
                                  text_message="Successfully retrieved user details")


@app.route("/user/profile/edit", methods=["POST"])
@user_jwt_token_required
@request_json_data_required(string_fields=["nickname", "text_status"])
def user_profile_edit(user_details: jwt_token_schemas.JWTTokenRegisteredUser, nickname: str, text_status: str,
                      db: Session = get_db()):
    """ Edit user's profile ( nickname + status )
    """
    user_updated_details = users_table_schemas.UserUpdateBaseModule(
        user_id=user_details.user_id,
        nickname=nickname,
        text_status=text_status,
    )
    try:
        updated_user_details: models.User = users_table_crud_commands.edit_user(
            db=db,
            user_details=user_updated_details
        )
        return updated_user_details.json()
    except users_table_crud_commands.UserNotFoundException:
        return custom_response_format(status_code=404,
                                      content=None,
                                      text_message="User not found with given ID",
                                      is_success=False)
    except users_table_crud_commands.UserFailedDatabaseUpdateException:
        return custom_response_format(status_code=500,
                                      content=None,
                                      text_message="Failed updating user in DB, try again",
                                      is_success=False)


@app.route("/users_details/", methods=["GET"])
@user_jwt_token_required
def users_details(user_details: jwt_token_schemas.JWTTokenRegisteredUser, db: Session = get_db()):
    """ Prints a list of all existing users

    """
    users_list: List[models.User] = users_table_crud_commands.get_users_list(db=db, skip=0, limit=100)
    users_list_json: List[Dict] = [user.json() for user in users_list]
    return custom_response_format(status_code=200,
                                  content=users_list_json,
                                  text_message="Successfully got users details list")


@app.route("/users_details/<int:user_id>", methods=["GET"])
@user_jwt_token_required
def user_details_id(user_details: jwt_token_schemas.JWTTokenRegisteredUser, user_id: int, db: Session = get_db()):
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
def admin_setup_database():
    """ Setups the database by creating its tables
    This should be run only on first bootstrap of the application
    """
    models.Base.metadata.create_all(bind=engine)
    return {"message": "Finished creating tables"}


@app.route("/admin/debug/read_jwt", methods=["GET"])
@user_jwt_token_required
def admin_debug_read_jwt(user_details: jwt_token_schemas.JWTTokenRegisteredUser):
    """ Shows user's details according to JWT token + validating the JWT token

    Validation done by the decorator attached to this route
    :return:
    """
    return custom_response_format(status_code=200,
                                  content=user_details,
                                  text_message="Successfully read user details")


@app.route("/admin/debug/all_messages", methods=["GET"])
@user_jwt_token_required
def admin_debug_all_messages(user_details: jwt_token_schemas.JWTTokenRegisteredUser, db: Session = get_db()):
    """ Shows all messages sent ever """
    messages_list: List[models.Message] = messages_table_crud_commands.get_messages(db=db)
    messages_list_json: List[Dict] = [message.json() for message in messages_list]
    return custom_response_format(status_code=200,
                                  content=messages_list_json,
                                  text_message="Successfully got messages list")


@app.route("/messages/message", methods=["POST"])
@user_jwt_token_required
@request_json_data_required(string_fields=["message_content", "receiver_id"])
def messages_send_message(user_details: jwt_token_schemas.JWTTokenRegisteredUser,
                          message_content: str,
                          receiver_id: int,
                          db: Session = get_db()):
    """ Allows a user to send a message to another user """
    message_to_add = messages_table_schemas.CreateMessageBaseModal(
        message_content=message_content,
        sender_id=user_details.user_id,
        receiver_id=receiver_id,
    )
    message_details: models.Message = messages_table_crud_commands.create_message(db=db, message=message_to_add)
    return custom_response_format(status_code=200,
                                  content=message_details.json(),
                                  text_message="Successfully sent message")


@app.route("/messages/message/<int:message_id>", methods=["DELETE"])
@user_jwt_token_required
def messages_delete_message(user_details: jwt_token_schemas.JWTTokenRegisteredUser,
                            message_id: int,
                            db: Session = get_db()):
    """ Deletes a message sent by a user

    A user can only delete messages sent by him
    """
    try:
        sender_id: int = user_details.user_id
        if not messages_table_crud_commands.is_message_sent_by_user(db=db, message_id=message_id, sender_id=sender_id):
            return custom_response_format(status_code=403,
                                          content=None,
                                          is_success=False,
                                          text_message=f"No permissions to delete message - user {sender_id} "
                                                       f"is not the user who sent message {message_id}")
        deleted_message_details: models.Message = messages_table_crud_commands.delete_message(
            db=db,
            message_id=message_id
        )
        return custom_response_format(status_code=200,
                                      content=deleted_message_details.json(),
                                      text_message="Successfully deleted message")
    except messages_table_crud_commands.MessageNotFoundException:
        return custom_response_format(status_code=404,
                                      content=None,
                                      is_success=False,
                                      text_message="No message with such ID")


@app.route("/messages/message/<int:message_id>", methods=["POST"])
@user_jwt_token_required
@request_json_data_required(string_fields=["message_content"])
def messages_update_message(user_details: jwt_token_schemas.JWTTokenRegisteredUser,
                            message_id: int,
                            message_content: str,
                            db: Session = get_db()):
    """ Updates a message sent by a user

    A user can only edit a message sent by him
    """
    try:
        sender_id: int = user_details.user_id
        if not messages_table_crud_commands.is_message_sent_by_user(db=db, message_id=message_id, sender_id=sender_id):
            return custom_response_format(status_code=403,
                                          content=None,
                                          is_success=False,
                                          text_message=f"No permissions to edit message - user {sender_id} "
                                                       f"is not the user who sent message {message_id}")
        updated_message_details: models.Message = messages_table_crud_commands.edit_message(
            db=db,
            message_id=message_id,
            message_content=message_content,
        )
        return custom_response_format(status_code=200,
                                      content=updated_message_details.json(),
                                      text_message="Successfully edited message")
    except messages_table_crud_commands.MessageNotFoundException:
        return custom_response_format(status_code=404,
                                      content=None,
                                      is_success=False,
                                      text_message="No message with such ID")
    except messages_table_crud_commands.MessageFailedDatabaseUpdateException:
        return custom_response_format(status_code=500,
                                      content=None,
                                      is_success=False,
                                      text_message="Failed updating the message due to application issues - try again")


@app.route("/chats", methods=["GET"])
@user_jwt_token_required
def chats_list(user_details: jwt_token_schemas.JWTTokenRegisteredUser,
               db: Session = get_db()):
    """ Return a list of all chats user is having with other users ( without returning the messages themselves but only
    a list of users who interacted with the logged-in user )
    """
    user_id: int = user_details.user_id
    chat_list = messages_table_crud_commands.get_user_chats_list(user_id=user_id, db=db)
    return custom_response_format(status_code=200,
                                  content=chat_list,
                                  text_message=f"Successfully returned chats list for user {user_id}")


@app.route("/chats/<int:receiver_id>", methods=["GET"])
@user_jwt_token_required
def chats_history_between_users(user_details: jwt_token_schemas.JWTTokenRegisteredUser,
                                receiver_id: int,
                                db: Session = get_db()):
    """ Shows chat history of two users ( all messages sent and accepted between a user and another user )

    sender ID - the logged-in user identified yb JWT token
    receiver ID - the other user who sends messages to the user
    """
    sender_id: int = user_details.user_id
    chat_messages_list: List[models.Message] = messages_table_crud_commands.get_user_chat_history_with_other_user(
        sender_id=sender_id,
        receiver_id=receiver_id,
        db=db,
    )
    chat_messages_list_json: List[Dict] = [message.json() for message in chat_messages_list]
    return custom_response_format(status_code=200,
                                  content=chat_messages_list_json,
                                  text_message=f"Successfully got chat messages list "
                                               f"between {sender_id} and {receiver_id}")


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
                                  text_message="Wrong authorization header value ( Probably expired / wrong token ) - "
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
    """ Raises when a client reqeust is missing a header named "Authorization"

    In CHAT BE APP - any route which requires Authorization header should be - "Authorization: Bearer <JWT token>"
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing authorization header - following header should be attached "
                                               "to a request \"Authorization: Bearer <JWT token>\"")


@app.errorhandler(ContentTypeHeaderNotExistException)
def exception_handler_content_type_header_not_exist(exception):
    """ Raises when a client reqeust is missing a header named "Content-Type" ( Required for JSON HTTP requests ) """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing Content-Type header - following header should be attached "
                                               "to a request \"Content-Type: application/json\"")


@app.errorhandler(ContentTypeHeaderHasWrongValueException)
def exception_handler_content_type_header_has_wrong_value(exception):
    """ Raises when a client reqeust has "Content-Type" header with value other than "application/json" ( Required for
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
    """ Raises when a client reqeust has JSON data with fields which have wrong type values ( For example a filed which
    should have a string value is having an int value, and vice versa )

    Relates to decorator @request_json_data_required which read JSON data from HTTP requests sent by clients.
    """
    return custom_response_format(status_code=400,
                                  is_success=False,
                                  text_message="Missing JSON data fields in the HTTP request!")
