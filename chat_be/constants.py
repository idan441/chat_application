from typing import Dict


"""
Constants file CHAT BE service
"""


# ## JWT token identity constants -  used by class JWTIssuer ###
class JWTTypes:
    """ Constants used for a field called "token_type" which is used to differ different token types issued by the
    auth service. These values should be used to evaluate JWT tokens by other microservices using the auth service """

    # These will be used added to the JWT token payload - i.e. {"token_type": "registered_user"}
    TOKEN_TYPE_DICT_KEY: str = "token_type"
    REGISTERED_USER_KEY_VALUE: str = "registered_user"
    MICROSERVICE_KEY_VALUE: str = "microservice"

    # This DICTs will be added to the JWT token by JWTIssuer class
    REGISTERED_USER: Dict[str, str] = {TOKEN_TYPE_DICT_KEY: REGISTERED_USER_KEY_VALUE}
    MICROSERVICE: Dict[str, str] = {TOKEN_TYPE_DICT_KEY: MICROSERVICE_KEY_VALUE}


class MicroServicesNames:
    """ List of registered microservices in the project.
    These microservices can communicate with each other based on microservice JWT tokens issued by AUTH SERVICE.
    Each of these JWT tokens will have a field named "service_name" with one of the above values.
    """
    USERS_MANAGER = "user_manager"
    CHAT_BE = "chat_be"
