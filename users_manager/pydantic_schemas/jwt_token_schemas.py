from pydantic import BaseModel


"""
Schemas for JWT token used in the project

There are two formats in this project -
1) microservice JWT tokens used for interaction between microservices
2) registered user JWT tokens - used by users
USER MANAGER service uses only microservice JWT tokens
"""


class JWTTokenMicroService(BaseModel):
    """ Represent a microservice JWT token values. This should be created after validating the JWT token. """
    token_type: str
    service_name: str
