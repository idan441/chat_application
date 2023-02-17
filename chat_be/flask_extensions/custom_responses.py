from typing import Union, Dict, List, Optional
from pydantic import BaseModel
from loguru import logger


"""
Custom responses formats for the CHAT BE application
"""


def custom_response_format(status_code: int,
                           content: Optional[Union[BaseModel, Dict[str, any], List[Dict[str, any]], str]] = None,
                           is_success=True,
                           text_message=None):
    """ Will format a Flask response to a united format of the CHAT BE application

    This also extends Flask response functionality - response can be either returned as a str, dict or as a Pydantic
    Base Module - in both case the method will JSON format the response.

    :return:
    """
    logger.info(f"Response returned with status code: {status_code} , "
                f"is_success: {is_success}, text_message: {text_message}")
    if issubclass(type(content), BaseModel):
        content = content.json()

    response_format: Dict[str, any] = {
        # A general format for all HTTP responses given by the CHAT BE application
        "request_uuid": "123",
        "is_success": is_success,
        "text_message": text_message,
        "content": content,
    }

    return response_format, status_code
