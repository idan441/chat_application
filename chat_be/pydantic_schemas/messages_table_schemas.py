from pydantic import BaseModel


"""
Pydantic base models for messages table in the MySQL DB of CHAT BE microservice
"""


class MessageIdBaseModal(BaseModel):
    """ A pydantic base model which includes only a message ID. Will be used to query a single message. """
    message_id: int


class CreateMessageBaseModal(BaseModel):
    """ A pydantic base model which to create a new message. """
    message_content: str
    sender_id: int
    receiver_id: int


class UpdateMessageBaseModal(BaseModel):
    """"""
