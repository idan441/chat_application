from typing import Union, List
import uuid
from loguru import logger
from functools import wraps

from flask import Flask, make_response, Response, request

from sqlalchemy.orm import Session, scoped_session
from mysql_connector import models
from mysql_connector.database import SessionLocal, engine, sessionmaker
from mysql_connector import messages_table_crud_commands, users_table_crud_commands
from pydantic_schemas import messages_table_schemas, users_table_schemas
# from init_objects import jwt_validator

from flask_sqlalchemy import SQLAlchemy



""""
CHAT BACKEND service - handles users requests and manages messages DB
"""


# Dependency
def get_db():
    with SessionLocal() as session:
        return session


app = Flask(__name__)


# def jwt_token_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if g.user is None:
#             return redirect(url_for('login', next=request.url))
#         return f(*args, **kwargs)
#     return decorated_function



@app.route("/user/login", methods=["GET"])
def user_login():
    """ Logins the user

    :return:
    """
    resp: Response = make_response("1")
    resp.set_cookie('user_id', "aaaa")
    return resp


@app.route("/user/profile", methods=["GET"])
def user_profile(db: Session = get_db()):
    """ Prints user's profile
    """
    # user_id: int = int(request.cookies.get('user_id'))

    user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=1)
    return user_details


@app.route("/admin/setup/database")
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
#
#
# @app.get("/users_profile/{user_id}")
# def get_user_profile(user_id: int, db: Session = Depends(get_db)):
#     """ Prints user's profile
#     """
#     user_details: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=user_id)
#     return user_details
#
#
# @app.post("/users_profile/login")
# def get_public_key():
#     """ Logins a user
#     This will authenticate user by username and password, will contact USER MANAGER service to verify user's identity,
#     will require a user JWT token from AUTH SERVICE, and will return it to the user so he can use the application
#     """
#     return {1:1}
#
#
# @app.get("/admin/setup/database")
# async def setup_database():
#     """ Setups the database by creating its tables
#     This should be run only on first bootstrap of the application
#     """
#     models.Base.metadata.create_all(bind=engine)
#     return {"message": "Finished creating tables"}
#
#
# @app.get("/test")
# async def setup_database(db: Session = Depends(get_db)):
#     """ Setups the database by creating its tables
#     This should be run only on first bootstrap of the application
#     """
#     aa = messages_table_crud_commands.get_messages(db=db, sender_id=1)
#     return aa
