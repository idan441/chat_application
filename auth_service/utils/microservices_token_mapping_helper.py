import os
from typing import Dict
from loguru import logger


"""
Helper class to read shared tokens from ENV VARs and pass them to JWTIssuer class
"""


class MicroservicesTokenMappingHelper:
    """ Helper class which reads the shared tokens from ENV VARs and returns a dictionary with the microservices code
     names and their respective shared token.

     This should be used solely by JWTIssuer class
     """
    def __init__(self, microservice_tokens_env_vars_dict: Dict[str, str]):
        """

        :param microservice_tokens_env_vars_dict: A dictionary of micro
        """
        self.microservice_tokens_env_vars_dict: Dict[str, str] = microservice_tokens_env_vars_dict

        self._microservices_mapping_dict: Dict[str, str] = {}

    def read_token_from_env_vars(self) -> None:
        """ Will read the ENV VARs representing the shared secrets tokens, and will update the mapping dictionary of
        microservices and tokens.

        :return: None
        """
        for microservice_code_name, shared_token_env_var in self.microservice_tokens_env_vars_dict.items():
            logger.debug(f"Reading shared secret for microservice {microservice_code_name} "
                         f"with ENV VAR {shared_token_env_var}")
            self._microservices_mapping_dict[microservice_code_name] = os.environ[shared_token_env_var]

        return None

    @property
    def microservices_mapping_dict(self) -> Dict[str, str]:
        """ Returns a dictionary with microservices code name ( a string represents them in the JWT tokens issued by
        AUTH SERVICE) and the shared tokens shared between them and AUTH SERVICE.

        :return: Dict[str, str]
        """
        return self._microservices_mapping_dict
