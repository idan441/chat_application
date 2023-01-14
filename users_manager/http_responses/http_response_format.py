import datetime
from typing import Dict
import uuid


""""
JSON format for the HTTP responses returned to clients by the USERS MANAGER application
"""


def format_http_response(response_dict: Dict[str, any]):
    """ Will return data in a general format for all HTTP requests """
    response_dict: Dict = {"uuid": uuid.uuid4(),
                           "response_time": str(datetime.time),
                           "content": response_dict,
                           "response_code": "GET_USER"}
    return response_dict
