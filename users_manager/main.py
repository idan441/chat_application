import os
from typing import List
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from loguru import logger

from sqlalchemy.orm import Session
from mysql_connector import users_table_crud_commands, models
from pydantic_schemas import users_schemas, admin_login_schemas, http_responses_shcemas
from mysql_connector.database import SessionLocal, engine
from logger.custom_logger import configure_custom_logger


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


load_dotenv()
app = FastAPI()
configure_custom_logger(logs_file_path=os.environ["LOGS_FILE_PATH"])


@app.middleware("http")
async def http_middleware(request: Request, call_next):
    """ Sets a middleware for the FastAPI server. Also adds a contextualized logging level """
    with logger.contextualize(request_uuid=uuid.uuid4()):
        logger.info(request.base_url)
        response: Response = await call_next(request)
        logger.info(f"status_code: {response.status_code}")
    return response


@app.get("/admin/users/get", response_model=http_responses_shcemas.HTTPTemplateBaseModelListUsersDetails)
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """ Returns a list of all users. Optional: filter by user ID or email """
    users: List[models.User] = users_table_crud_commands.get_users_list(db, skip=skip, limit=limit)
    return http_responses_shcemas.HTTPTemplateBaseModelListUsersDetails(
        content=users,
        text_message="Successfully returned users list"
    )


@app.post("/admin/users/create", response_model=http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails)
def create_user(user: users_schemas.UserCreateBaseModule, db: Session = Depends(get_db)):
    """ Creates a new user """
    db_user: models.User = users_table_crud_commands.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail={1: "Email already registered"})
    return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
        content=users_table_crud_commands.create_user(db=db, user=user),
        text_message="User created successfully!"
    )


@app.post("/admin/users/edit", response_model=http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails)
def edit_user(user: users_schemas.UserUpdateBaseModule, db: Session = Depends(get_db)):
    """ Edits a user """
    updated_user: models.User = users_table_crud_commands.edit_user(db, user=user)
    return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
        content=updated_user,
        text_message="User updated successfully!"
    )


@app.delete("/admin/users/delete")
def delete_user(user: users_schemas.UserIdBaseModal, db: Session = Depends(get_db)):
    """ Deletes a user """
    db_user: models.User = users_table_crud_commands.get_user_by_id(db, user_id=user.user_id)
    if db_user:
        return users_table_crud_commands.delete_user(db=db, user=user)
    raise HTTPException(status_code=400, detail="User isn't found")


@app.post("/admin/login")
async def root(login_details: admin_login_schemas.LoginDetailsModal):
    """ Logins the admin and returning it an access token """
    username: str = login_details.username
    password: str = login_details.password
    if username == os.environ["ADMIN_USERNAME"] \
            and password == os.environ["ADMIN_PASSWORD"]:
        return {"message": "YES"}
    else:
        raise HTTPException(status_code=404, detail={"message": "NO"})


@app.get("/admin/setup/database")
async def root():
    """ Setups the database by creating its tables
    This should be run only on first bootstrap of the application
    """
    models.Base.metadata.create_all(bind=engine)
    return {"message": "Finished creating tables"}


@app.get("/admin/logout")
async def root():
    """ Log out a user by deleting his session cookies """
    return {"message": "Hello World"}


@app.post("/chat_be/authenticate")
async def chat_be_authenticate():
    """ Returns a token for other microservices accessing the USER MANAGER application. The token will be used to query
    the service """
    return {"message": "Hello World"}


@app.get("/chat_be/user/{user_id}", response_model=http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails)
def chat_be_read_user(user_id: int, db: Session = Depends(get_db)):
    """ Returns a specific user details by its user ID """
    db_user = users_table_crud_commands.get_user_by_id(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
