from typing import Dict


"""
Constants file for auth service
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


class MicroservicesCodeNames:
    """ List of registered microservices in the project.
    These microservices can communicate with each other based on microservice JWT tokens issued by AUTH SERVICE.
    Each of these JWT tokens will have a field named "service_name" with one of the above values.
    """
    USERS_MANAGER = "user_manager"
    CHAT_BE = "chat_be"


class MicroservicesTokenMapping:
    """ Represent a mapping of microservices code names and their shared token with AUTH SERVICE
    The secret tokens are used to authenticate microservice in front of AUTH SERVICE
    """

    """ Authentication tokens used by different microservices in the project in order to authenticate with auth service
        and issue a JWT token for themselves.
        
        This mapping contains -
        1) microservice code name - a string representing the microservice in all JWT tokens issued by AUTH SERVICE
           and is used by microservice to authenticate in front of AUTH SERVICE to issue a token for themselves.
        2) The ENV VAR which contains a shared token between the microservice and AUTH SERVICE. This will be used by
           microservices to authenticate in front of AUTH SERVICE.
           * Note - the ENV VAR itself will be read at init_objects.py file after loading them using dotenv package
        """
    MICROSERVICES_TOKENS_ENV_VARS_DICT: Dict[str, str] = {
        MicroservicesCodeNames.USERS_MANAGER: "AUTH_SERVICE_USER_MANAGER_SHARED_SECRET",
        MicroservicesCodeNames.CHAT_BE: "AUTH_SERVICE_CHAT_BE_SHARED_SECRET",
    }
