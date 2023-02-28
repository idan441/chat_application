from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
import sqlalchemy.exc as sqlalchemy_exceptions
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy import func, or_
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
    :raises MessageNotFoundException: In case message_id does not in messages table
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


def delete_message(db: Session, message_id: int) -> models.Message:
    """ Deletes an existing message in the messages table

    :param db:
    :param message_id:
    :raises MessageNotFoundException: In case message_id doesn't exist in messages table
    :return: deleted message details
    """
    message: models.User = get_message_by_id(db=db, message_id=message_id)
    db.delete(message)
    db.commit()
    return message


def edit_message(db: Session, message_id: int, message_content: str) -> models.Message:
    """ Edits an existing message in the messages table

    :param db:
    :param message_id:
    :param message_content: New content for the message
    :raises MessageNotFoundException: In case message_id does not in messages table
    :raises MessageFailedDatabaseUpdateException: In case failed to update the message due to DB issues
    :return: edited message updated details
    """
    db_message: models.Message = get_message_by_id(db=db, message_id=message_id)
    db_message.message_content = message_content

    try:
        db.flush()
        db.commit()
    except sqlalchemy_exceptions.IntegrityError:
        db.rollback()
        raise MessageFailedDatabaseUpdateException()
    return db_message


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


def is_message_sent_by_user(db: Session, sender_id: int, message_id: int) -> bool:
    """ Check if a message was sent by a user, return a bool value

    This will be used to verify permissions of user to delete/edit a message - as he can only do this ot messages sent
    by him. If message id doesn't exist then will raise


    :param db:
    :param sender_id:
    :param message_id:
    :raises MessageNotFoundException: In case message_id does not in messages table
    :return: bool - true if message was sent by user
    """
    message: models.Message = get_message_by_id(db=db, message_id=message_id)
    logger.debug(f"Checking if {message_id} was sent by user {sender_id} - message details: {message.json()}")
    if int(message.sender_id) == sender_id:
        logger.debug(f"Message {message_id} was indeed sent by user {sender_id} - returning 'True'")
        return True
    logger.debug(f"Message {message_id} was not sent by user {sender_id} - returning 'False'")
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


def get_user_chats_list(db: Session, user_id: int) -> List[Dict[str, any]]:
    """ Will return a list of all users who have a chat with a user + their details + statistics.
    This will be used to list the chats in the application UI, where the user can choose to view a specific chat history

    :param db:
    :param user_id:
    :return: A list of dicts with details about each chat of a user with another user
    """
    logger.debug(f"Looking for chats list for user {user_id}")
    # TODO - improve it
    query = db.query(
        models.Message.receiver_id,
        models.Message.sender_id,
        func.count(models.Message.message_id),
        func.max(models.Message.sent_datetime)
    ).filter(
        or_(models.Message.sender_id == user_id, models.Message.receiver_id == user_id)
    ).group_by(
        models.Message.receiver_id
    ).all()

    dict_results_list = []
    for row in query:
        receiver_id, sender_id, message_count, newest_message = row
        dict_results_list.append(
            {
                "receiver_id": receiver_id,
                "sender_id": sender_id,
                "messages_count": message_count,
                "newest_message": newest_message,
            }
        )

    logger.debug(f"Returned following chats list returned for user {user_id} : {dict_results_list}")
    return dict_results_list


def get_user_chat_history_with_other_user(db: Session, receiver_id: int, sender_id: int) -> List[models.Message]:
    """ Returns all messages chat history between two users ( Including the case of each user being the sender or
    receiver - that is both messages sent by user A to B and from user B to A will be included )

    :param db:
    :param receiver_id:
    :param sender_id:
    :return:
    """
    messages_sent_by_receiver: List[models.Message] = get_messages(db=db,
                                                                   receiver_id=receiver_id,
                                                                   sender_id=sender_id)
    messages_sent_by_sender: List[models.Message] = get_messages(db=db,
                                                                 receiver_id=sender_id,
                                                                 sender_id=receiver_id)
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
