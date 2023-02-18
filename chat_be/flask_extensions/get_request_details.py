from typing import List, Dict, Union
from flask import request


"""
Methods for reading and validating input sent with a Flask client reqeust, as headers or body
"""


class HeaderNotExistException(Exception):
    """ Raises in case a header field is not included in a client request
    Example: trying to read an "Authorization" header from a request and the header doesn't exist. """
    pass


class ContentTypeHeaderNotExistException(Exception):
    """ Raises in case a "Content-Type" header field doesn't exist but supposed to be sent by the client """
    pass


class ContentTypeHeaderHasWrongValueException(Exception):
    """ Raises in case a "Content-Type" header field sent by the client has wrong value ( Needs to be "application/json"
     as the CHAT BE service supports only this format. ) """
    pass


class MissingRequestJSONDataField(Exception):
    """ Raises when a needed JSON data field is missing in the request sent by the client
    Used by method get_request_body() """


class JSONDataFieldWrongValue(Exception):
    """ Raises when a needed JSON data field has a wrong type value in the request sent by the client
    Example: if user need to send a JSON data with string value and instead send an int one.
    Used by method get_request_body() """


def get_header_value_from_request(header_name: str) -> str:
    """ Returns a value in the headers of a client request

    :param header_name:
    :raises HeaderNotExistException: in case header name doesn't exist in the client request sent to Flask
    :return: str - header value
    """
    try:
        header_value: str = request.headers[header_name]
        return header_value
    except KeyError:
        raise HeaderNotExistException(f"Could not find a header with name \"{header_name}\" in the client request")


def get_request_body(string_fields: List[str], int_fields: List[str]):
    """ Gets request JSON data from the Flask reqeust and verifies its type. (str/int)

    Note - this is a Flask app, therefor it will be able to read the JSON data only if the header "Content-Type" is
           attached with value "application/json" ! Therefore, the method verifies this header exist

    :param string_fields: field names which should include a string value
    :param int_fields: field names which should include an int value
    :raises ContentTypeHeaderNotExistException: In case header "Content-Type" is missing
    :raises ContentTypeHeaderHasWrongValueException: In case "Content-Type" is not "application/json"
    :raises ContentTypeHeaderHasWrongValueException: If "Content-Type" header is not "application/json"
    :raises ContentTypeHeaderNotExistException: If missing "Content-Type" header
    :return: A dictionary with field names (combined for str and int fields given) and their values
    """
    try:
        content_type_header_value: str = get_header_value_from_request(header_name="Content-Type")
        if content_type_header_value != "application/json":
            raise ContentTypeHeaderHasWrongValueException("Header \"Content-Type\" needs to be \"application/json\"")
    except HeaderNotExistException:
        raise ContentTypeHeaderNotExistException("Missing header \"Content-Type: application/json\"")

    # Read fields from the Flask request
    variables_to_pass: Dict[str, Union[str, int]] = {}
    if string_fields:
        for field in string_fields:
            try:
                variables_to_pass[field] = str(request.json[field])
            except KeyError:
                raise MissingRequestJSONDataField(f"Missing field with name {field} "
                                                  f"in the JSON data sent! (Value should be string)")
            except ValueError:  # TODO - check if need to test anything for string - anyway it is a string!
                raise JSONDataFieldWrongValue(f"Value of field {field} is not string")

    if int_fields:
        for field in int_fields:
            try:
                field_value = request.json[field]
                if field_value.is_numeric():  # TODO - change to have a better check with regex (  Because "\u0030" which is unicode for 0 is also True )
                    variables_to_pass[field] = int(field_value)
                else:
                    raise JSONDataFieldWrongValue(f"Value of field {field} is not int")

            except KeyError:
                raise MissingRequestJSONDataField(f"Missing field with name {field} "
                                                  f"in the JSON data sent! (Value should be int)")

    return variables_to_pass


