import uuid
from werkzeug.wrappers import Request, Response, ResponseStream
from loguru import logger


"""
Create a middleware for the CHAT BE service
The middleware is imported to main.py where it is attached to the Flask application
"""


class FlaskMiddleware:
    """ Middleware for CHAT BE service """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        with logger.contextualize(request_uuid=uuid.uuid4()):
            return self.app(environ, start_response)
