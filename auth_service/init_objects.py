import os
from dotenv import load_dotenv


from logger.custom_logger import configure_custom_logger
from utils.jwt_issuer import JWTIssuer
from fast_api_extensions.auth_http_request import AuthHTTPRequest


"""
Will create some objects which are needed to run the AUTH SERVICE application
Reason for using this file and not main.py is because it needs to be imported by other modules too.
"""


load_dotenv()
configure_custom_logger(logs_file_path=os.environ["LOGS_FILE_PATH"])

jwt_issuer = JWTIssuer(private_key=os.environ["JWT_PRIVATE_KEY"],
                       public_key=os.environ["JWT_PUBLIC_KEY"],
                       key_algorithm=os.environ["KEY_ALGORITHM"],
                       expiration_time_in_hours=int(os.environ["JWT_VALIDITY_IN_HOURS"]))
auth_http_request = AuthHTTPRequest(jwt_issuer=jwt_issuer)
