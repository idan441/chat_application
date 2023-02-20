import os
from typing import List, Union
import uuid
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status as HTTP_STATUS_CODES
from loguru import logger

from sqlalchemy.orm import Session
from mysql_connector import users_table_crud_commands, models
from pydantic_schemas import users_schemas, admin_login_schemas, http_responses_shcemas
from mysql_connector.database import SessionLocal, engine
from fast_api_extensions.fast_api_dependencies import require_chat_be_microservice_jwt_token


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.middleware("http")
async def http_middleware(request: Request, call_next):
    """ Sets a middleware for the FastAPI server. Also adds a contextualized logging level """
    with logger.contextualize(request_uuid=uuid.uuid4()):
        logger.info(request.base_url)
        response: Response = await call_next(request)
        logger.info(f"status_code: {response.status_code}")
    return response


@app.get("/admin/users/get",
         status_code=HTTP_STATUS_CODES.HTTP_200_OK,
         response_model=http_responses_shcemas.HTTPTemplateBaseModelListUsersDetails)
def get_users_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """ Returns a list of all users. Optional: filter by user ID or email """
    users: List[models.User] = users_table_crud_commands.get_users_list(db, skip=skip, limit=limit)
    return http_responses_shcemas.HTTPTemplateBaseModelListUsersDetails(
        content=users,
        text_message="Successfully returned users list"
    )


@app.get("/admin/users/get/{user_id}",
         status_code=HTTP_STATUS_CODES.HTTP_200_OK,
         response_model=Union[http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails,
                              http_responses_shcemas.HTTPTemplateBaseModelError])
def read_user_details_by_id(user_id: int, response: Response, db: Session = Depends(get_db)):
    """ Returns user details based on user ID """
    try:
        user: models.User = users_table_crud_commands.get_user_by_id(db, user_id=user_id)
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=user,
            text_message="Successfully returned user details"
        )
    except users_table_crud_commands.UserNotFoundException:
        response.status_code = HTTP_STATUS_CODES.HTTP_404_NOT_FOUND
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            text_message="User does not exist",
            is_success=False,
        )


@app.post("/admin/users/create",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=Union[http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails,
                               http_responses_shcemas.HTTPTemplateBaseModelError])
def create_user(user: users_schemas.UserCreateBaseModule, response: Response, db: Session = Depends(get_db)):
    """ Creates a new user """
    # TODO - consider dropping it - as any created user should be in CHAT BE database too! Or on the other hand need UM
    #                               to send a request to CHAT BE! Preferably have two options
    try:
        created_user_details: models.User = users_table_crud_commands.create_user(db=db, user=user)
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=created_user_details,
            text_message="User created successfully"
        )
    except users_table_crud_commands.EmailAddressAlreadyExistsException:
        response.status_code = HTTP_STATUS_CODES.HTTP_400_BAD_REQUEST
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            text_message="Email already registered with an existing user",
            is_success=False,
        )


@app.post("/admin/users/edit",
          status_code=HTTP_STATUS_CODES.HTTP_200_OK,
          response_model=Union[http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails,
                               http_responses_shcemas.HTTPTemplateBaseModelError])
def edit_user(user: users_schemas.UserUpdateBaseModule, response: Response, db: Session = Depends(get_db)):
    """ Edits a user """
    try:
        updated_user: models.User = users_table_crud_commands.edit_user(db, user=user)
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=updated_user,
            text_message="User updated successfully"
        )
    except users_table_crud_commands.EmailAddressAlreadyExistsException:
        response.status_code = HTTP_STATUS_CODES.HTTP_400_BAD_REQUEST
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=user,
            text_message="Failed creating user - given email belongs to an existing user",
            is_success=False
        )
    except users_table_crud_commands.UserFailedDatabaseUpdateException:
        response.status_code = HTTP_STATUS_CODES.HTTP_400_BAD_REQUEST
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            content=user,
            text_message="Failed updating user details, check parameters sent in the request",
            is_success=False,
        )
    except users_table_crud_commands.UserNotFoundException:
        response.status_code = HTTP_STATUS_CODES.HTTP_404_NOT_FOUND
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            text_message="User does not exists with this ID",
            is_success=False,
        )


@app.delete("/admin/users/delete",
            status_code=HTTP_STATUS_CODES.HTTP_200_OK,
            response_model=Union[http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails,
                                 http_responses_shcemas.HTTPTemplateBaseModelError])
def delete_user(user: users_schemas.UserIdBaseModal, response: Response, db: Session = Depends(get_db)):
    """ Deletes a user """
    try:
        deleted_user_details: models.User = users_table_crud_commands.delete_user(db=db, user=user)
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=deleted_user_details,
            text_message="User deleted successfully"
        )
    except users_table_crud_commands.UserNotFoundException:
        response.status_code = HTTP_STATUS_CODES.HTTP_404_NOT_FOUND
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            text_message="User does not exists with this ID",
            is_success=False,
        )


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
async def setup_database():
    """ Setups the database by creating its tables
    This should be run only on first bootstrap of the application
    """
    models.Base.metadata.create_all(bind=engine)
    return {"message": "Finished creating tables"}


@app.get("/admin/logout")
async def admin_logout():
    """ Logs out from admin panel by deleting his session cookies """
    return {"message": "Hello World"}


@app.get("/chat_be/user/details/{user_id}",
         status_code=HTTP_STATUS_CODES.HTTP_200_OK,
         response_model=Union[http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails,
                              http_responses_shcemas.HTTPTemplateBaseModelError])
def chat_be_user_details_by_id(user_id: int,
                      response: Response,
                      microservice_token: str = Depends(require_chat_be_microservice_jwt_token),
                      db: Session = Depends(get_db),):
    """ Returns user details by its user ID """
    try:
        user: models.User = users_table_crud_commands.get_user_by_id(db=db, user_id=user_id)
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=user,
            text_message="Successfully returned user details"
        )
    except users_table_crud_commands.UserNotFoundException:
        response.status_code = HTTP_STATUS_CODES.HTTP_404_NOT_FOUND
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            text_message="User does not exist",
            is_success=False,
        )


@app.post("/chat_be/users/create",
          status_code=HTTP_STATUS_CODES.HTTP_201_CREATED,
          response_model=Union[http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails,
                               http_responses_shcemas.HTTPTemplateBaseModelError])
def chat_be_create_user(user: users_schemas.UserCreateBaseModule,
                        response: Response,
                        microservice_token: str = Depends(require_chat_be_microservice_jwt_token),
                        db: Session = Depends(get_db)):
    """ Creates a new user

    This route should be used by CHAT BE service! CHAT BE also has a database which needs to create the user based on
    this route response.
    """
    try:
        created_user_details: models.User = users_table_crud_commands.create_user(db=db, user=user)
        return http_responses_shcemas.HTTPTemplateBaseModelSingleUserDetails(
            content=created_user_details,
            text_message="User created successfully"
        )
    except users_table_crud_commands.EmailAddressAlreadyExistsException:
        response.status_code = HTTP_STATUS_CODES.HTTP_400_BAD_REQUEST
        return http_responses_shcemas.HTTPTemplateBaseModelError(
            text_message="Email already registered with an existing user",
            is_success=False,
        )


@app.post("/chat_be/users/login",
          status_code=HTTP_STATUS_CODES.HTTP_200_OK,
          response_model=http_responses_shcemas.HTTPTemplateBaseModelUserLoginResponse)
def chat_be_user_login(user_details: users_schemas.UserLoginBaseModule,
                        response: Response,
                        microservice_token: str = Depends(require_chat_be_microservice_jwt_token),
                        db: Session = Depends(get_db)):
    """ Logins a new user

    This route should be used by CHAT BE service! It should send user credentials to UM service in order to verify the
    user authenticity and if is active
    """
    try:
        logged_in_user_details: models.User = users_table_crud_commands.get_user_by_email_and_password(
            db=db,
            email=user_details.email,
            password=user_details.password
        )
        if logged_in_user_details.is_active:
            return http_responses_shcemas.HTTPTemplateBaseModelUserLoginResponse(
                content=users_schemas.UserLoginResultBaseModule(
                    is_login_success=True,
                    is_active=True
                ),
                text_message="User details are correct and user is active - user can login to application"
            )
        else:
            return http_responses_shcemas.HTTPTemplateBaseModelUserLoginResponse(
                content=users_schemas.UserLoginResultBaseModule(
                    is_login_success=True,
                    is_active=False
                ),
                text_message="User details are correct but user is in active - therefore he can't connect",
            )
    except users_table_crud_commands.UserFailedLoginException:
        return http_responses_shcemas.HTTPTemplateBaseModelUserLoginResponse(
            content=users_schemas.UserLoginResultBaseModule(
                is_login_success=False,
                is_active=False
            ),
            text_message="Given details are wrong - either username or password are wrong",
        )
