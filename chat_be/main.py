from typing import Union
import uuid
from fastapi import FastAPI, Request, Response, Header, Depends, HTTPException, status as HTTP_STATUS_CODES
from loguru import logger


""""
CHAT BACKEND service - handles users requests and manages messages DB
"""


app = FastAPI()


@app.middleware("http")
async def http_middleware(request: Request, call_next):
    """ Sets a middleware for the FastAPI server. Also adds a contextualized logging level """
    with logger.contextualize(request_uuid=uuid.uuid4()):
        response: Response = await call_next(request)
        logger.info(f"status_code: {response.status_code}")
    return response


@app.get("/get_user_messages")
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    return {1:1}


@app.get("/send_message")
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    return {1:1}


@app.get("/active_users")
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    return {1:1}


@app.get("/users_profile")
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    return {1:1}


@app.get("/get_user_messages")
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    return {1:1}


@app.get("/get_login")
def get_public_key():
    """ Returns the public key used for authenticating the JWT tokens created by this service

    This route can be public, as the JWT tokens can only be signed with the private key which is known to this service
    only. By the least, this route should be available for other backend services who want to authenticate JWT tokens.
    """
    return {1:1}
