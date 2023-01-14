from loguru import logger


"""
Configures a custom configurations for the logger used by USER MANAGER application
Logging of the application is done using Loguru library
"""


def configure_custom_logger(logs_file_path: str) -> None:
    """ Will configure the logging module to use a JSON customized logging

    :param logs_file_path:
    :return: None
    """
    logger.remove(0)
    logger.add(logs_file_path,
               format="{time} | {level} | {extra[request_uuid]} | Message : {message}",
               colorize=False,
               serialize=True)

    return None
