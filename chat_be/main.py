from typing import Union, List, Dict
import uuid
from loguru import logger
from functools import wraps

from flask import Flask, make_response, Response, request, g, redirect, url_for
from flask_pydantic import validate as pydantic_validation

from sqlalchemy.orm import Session, scoped_session
from mysql_connector import models
from mysql_connector.database import SessionLocal, engine, sessionmaker
from mysql_connector import messages_table_crud_commands, users_table_crud_commands
from pydantic_schemas import messages_table_schemas, users_table_schemas, jwt_token_schemas, http_responses_schemas, \
    user_manager_service_responses_schemas
from init_objects import jwt_validator, auth_http_request, user_manager_integration
from utils.user_manager_integrations import FailedCreatingUserInUserManagerEmailAlreadyExistsException


""""
CHAT BACKEND service - handles users requests and manages messages DB
"""


# Dependency
def get_db():
    session = SessionLocal()
    return session


app = Flask(__name__)


@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop(name='db', default=None)

    if db is not None:
        db.close()


def user_jwt_token_required(f):
    """ Makes sure the HTTP request needs a user-type JWT token

    * Will validate the HTTP request sent by client includes a JWT token
    * will verify the JWT token is of type "registered_user" and will set the user details as Flask "g" so it will be
      available for routes to handle it.

    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization_header: str = request.headers["Authorization"]
        user_details: jwt_token_schemas.JWTTokenRegisteredUser = auth_http_request.verify_registered_user_jwt_token(
            authorization_bearer_header=authorization_header
        )
        g.user_details = user_details
        # if g.user is None:
        #     return "aadas"
            # return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/user/who_am_i", methods=["GET"])
@user_jwt_token_required
def user_who_am_i():
    """ Shows user's details according to JWT token + validating the JWT token

    :return:
    """
    return g.user_details.json()


@app.route("/user/login", methods=["POST"])
def user_login():
    """ Logins the user

    :return:
    """
    resp: Response = make_response("1")
    resp.set_cookie('user_id', "aaaa")
    return resp


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
def user_profile(db: Session = get_db()):
    """ Prints user's profile
    """
    user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=17)
    return user_details


@app.route("/users_details/", methods=["GET"])
# @pydantic_validation()
def users_details(db: Session = get_db()):
    """ Prints a list of all existing users

    """
    users_list: List[models.User] = users_table_crud_commands.get_users_list(db=db, skip=0, limit=100)
    users_list_json: List[Dict] = [user.json() for user in users_list]
    return users_list_json


@app.route("/users_details/<int:user_id>", methods=["GET"])
# @pydantic_validation()
def user_details_id(user_id: int, db: Session = get_db()):
    """ Prints a list of all existing users

    """

    try:
        user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=user_id)
        return user_details.json()
    except users_table_crud_commands.UserNotFoundException:
        return "User not found!"


@app.route("/admin/setup/database", methods=["GET"])
def setup_database():
    """ Setups the database by creating its tables
    This should be run only on first bootstrap of the application
    """
    models.Base.metadata.create_all(bind=engine)
    return {"message": "Finished creating tables"}


#
#
# app = FastAPI()
#
#
# @app.middleware("http")
# async def http_middleware(request: Request, call_next):
#     """ Sets a middleware for the FastAPI server. Also adds a contextualized logging level """
#     with logger.contextualize(request_uuid=uuid.uuid4()):
#         response: Response = await call_next(request)
#         logger.info(f"status_code: {response.status_code}")
#     return response
#
#
# @app.get("/user_messages/get_unread_messages/tmo-{receiver_id}")  # TODO - debugging, later hsould have user id when logged in + the other user
# def get_user_unread_messages(receiver_id: int, db: Session = Depends(get_db)):
#     """ Returns users unread messages """
#     messages: List[models.Message] = messages_table_crud_commands.get_user_unread_messages(db=db, receiver_user_id=receiver_id)
#     return messages
#
#
# @app.get("/user_messages/chat_history/{sender_id}/tmp-{receiver_id}")  # TODO - debugging, later hsould have user id when logged in + the other user
# def get_user_unread_messages(sender_id: int, receiver_id: int, db: Session = Depends(get_db)):
#     """ Returns users chat history with another user
#
#     :param sender_id: The other user who sent messages to the logged-in user
#     :param db:
#     :return:
#     """
#     chat_history_messages: List[models.Message] = messages_table_crud_commands.get_user_chat_history_with_other_user(
#         db=db,
#         sender_id=sender_id,
#         receiver_user_id=receiver_id
#     )
#     return chat_history_messages
#
#
# @app.post("/user_messages/send_message",
#           status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
#           )
# def post_send_message(message: messages_table_schemas.CreateMessageBaseModal, response: Response, db: Session = Depends(get_db)):
#     """ Creates a new message in a chat between two users """
#     created_message_details: models.Message = messages_table_crud_commands.create_message(db=db, message=message)
#     return created_message_details
