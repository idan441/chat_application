from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import sqlalchemy.exc as sqlalchemy_exceptions
from sqlalchemy.sql.elements import BinaryExpression
from loguru import logger

from . import models, users_table_crud_commands
from pydantic_schemas import users_table_schemas, messages_table_schemas

"""
Defines top-level methods for manipulating data in the messages table
"""


class MessageNotFoundException(Exception):
    """ Raises if querying for a message which doesn't exist in the messages table """
    pass


class MessageFailedDatabaseUpdateException(Exception):
    """ Raises if updating DB record for a message has failed due to DB query issue """
    pass


class MissingFilterParameterException(Exception):
    """ Raises if a method for updating the DB is not given enough parameters used to filter nrecord"""


def get_message_by_id(db: Session, message_id: int) -> models.Message:
    """ Returns a message details from the messages table according to its message ID

    :param db:
    :param message_id:
    :raises MessageNotFoundException: In case user_id not in users table
    :return:
    """
    message: models.Message = db.query(models.Message).filter(models.Message.message_id == message_id).first()
    if not message:
        raise MessageNotFoundException()
    return message


def create_message(db: Session, message: messages_table_schemas.CreateMessageBaseModal) -> models.Message:
    """ Creates a message in the messages table

    :param db:
    :param message:
    :return: created message details
    """
    message = models.Message(message_content=message.message_content,
                             sender_id=message.sender_id,
                             receiver_id=message.receiver_id)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def delete_message(db: Session, message_details: messages_table_schemas.MessageIdBaseModal) -> models.Message:
    """ Deletes an existing message in the messages table

    :param db:
    :param message_details: The message ID
    :raises MessageNotFoundException: In case message_id doesn't exist in messages table
    :return: user's updated details
    """
    # TODO - raise an exception if message not found
    message: models.User = get_message_by_id(db=db, message_id=message_details.message_id)
    db.delete(message)
    db.commit()
    return message


def is_message_exist_by_message_id(db: Session, message_id: int) -> bool:
    """ Checks if a message exists in the messages table according to message ID

    :param db:
    :param message_id:
    :return: boolean
    """
    try:
        get_message_by_id(db=db, message_id=message_id)
        return True
    except MessageNotFoundException:
        return False


def get_messages(db: Session,
                 sender_id: Optional[int] = None,
                 receiver_id: Optional[int] = None,
                 messages_ids: Optional[List[int]] = None,
                 messages_limit: Optional[int] = 1000,
                 filter_after_sent_date: Optional[datetime] = None,
                 filter_unread_messages_only: bool = False) -> List[models.Message]:
    """ Queries messages table for messages with specific filters

    :param db:
    :param messages_ids:
    :param sender_id:
    :param receiver_id:
    :param messages_limit:
    :param filter_after_sent_date:
    :param filter_unread_messages_only:
    :return:
    """
    logger.info("Searching for messages in messages table with following conditions: "
                f"sender_id: {sender_id} ,"
                f"receiver_id: {receiver_id} ,"
                f"messages_ids: {messages_ids} ,"
                f"messages_limit: {messages_limit} ,"
                f"messages_limit: {messages_limit} ,"
                f"filter_after_sent_date: {filter_after_sent_date} ,"
                f"filter_unread_messages_only: {filter_unread_messages_only} ,")

    params_to_search: List[BinaryExpression] = []
    if sender_id:
        params_to_search.append(models.Message.sender_id == sender_id)
    if receiver_id:
        params_to_search.append(models.Message.receiver_id == receiver_id)
    if messages_ids:
        params_to_search.append(models.Message.message_id.in_(messages_ids))
    if filter_after_sent_date:
        params_to_search += (models.Message.sent_datetime >= filter_after_sent_date)
    if filter_unread_messages_only:
        params_to_search += (not models.Message.is_message_read)

    messages: List[models.Message] = db.query(models.Message) \
        .filter(*params_to_search).limit(limit=messages_limit).all()

    return messages


def get_user_unread_messages(db: Session, receiver_user_id: int) -> List[models.Message]:
    """ Returns all unread messages sent to a user according to its ID

    :param db:
    :param receiver_user_id:
    :return:
    """
    messages: List[models.Message] = get_messages(db=db,
                                                  receiver_id=receiver_user_id,
                                                  filter_unread_messages_only=True)
    return messages


def get_user_chat_history_with_other_user(db: Session, receiver_user_id: int, sender_id: int) -> List[models.Message]:
    """ Returns all messages chat history between two users ( Including the case of each user being the sender or
    receiver - that is both messages sent by user A to B and from user B to A will be included )

    :param db:
    :param receiver_user_id:
    :param sender_id:
    :return:
    """
    messages_sent_by_receiver: List[models.Message] = get_messages(db=db,
                                                                   receiver_id=receiver_user_id,
                                                                   sender_id=sender_id)
    messages_sent_by_sender: List[models.Message] = get_messages(db=db,
                                                                 receiver_id=sender_id,
                                                                 sender_id=receiver_user_id)
    messages_combined: List[models.Message] = list(set(messages_sent_by_receiver).union(messages_sent_by_sender))
    return messages_combined


def mark_messages_as_read(db: Session,
                          messages_ids: Optional[List[int]] = None,
                          sender_id: Optional[int] = None,
                          receiver_id: Optional[int] = None) -> List[models.Message]:
    """ Will update messages and set them as read.

    Note - at least one filtering parameters must be given in the function. In case no filter is given - an exception
           will rais.
           If no messages are selected after the applied filters - will still return a successful response

    :param db:
    :param messages_ids:
    :param sender_id:
    :param receiver_id:
    :raises MissingFilterParameterException: In case no filter for messages is given in the method parameters
    :raises MessageFailedDatabaseUpdateException: In case updating DB fails
    :return:
    """

    if not (messages_ids or sender_id or receiver_id):
        raise MissingFilterParameterException()

    params_to_search: List[BinaryExpression] = []
    if sender_id:
        params_to_search.append(models.Message.sender_id == sender_id)
    if receiver_id:
        params_to_search.append(models.Message.receiver_id == receiver_id)
    if messages_ids:
        params_to_search.append(models.Message.message_id.in_(messages_ids))

    updated_messages: List[models.Message] = db.query(models.Message) \
        .filter(*params_to_search). \
        update(values={models.Message.is_message_read: True, models.Message.received_datetime: datetime.now()}).all()

    try:
        db.flush()
        db.commit()
    except sqlalchemy_exceptions.IntegrityError:
        db.rollback()
        raise MessageFailedDatabaseUpdateException()
    return updated_messages
