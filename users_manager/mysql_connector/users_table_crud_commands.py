from typing import List
from sqlalchemy.orm import Session
import sqlalchemy.exc as sqlalchemy_exceptions

from . import models
from pydantic_schemas import users_schemas


"""
Defines top-level methods for manipulating data in the users table
"""


class UserNotFoundException(Exception):
    """ A custom exception which raises if querying the users table and user isn't found """
    pass


class UserFailedDatabaseUpdateException(Exception):
    """ A custom exception which raises if updating DB record for user has failed due to DB query issue """
    pass


class EmailAddressAlreadyExistsException(Exception):
    """ A custom exception which raises if trying to update or create a user and assign it an email address which
     already used by another user ( email address is a unique column in the DB and can't exist for two users ) """
    pass


def get_user_by_id(db: Session, user_id: int) -> models.User:
    """ Returns a user's details from the users table according to his user ID

    :param db:
    :param user_id:
    :raises UserNotFoundException: In case user_id not in users table
    :return:
    """
    user: models.User = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise UserNotFoundException()
    return user


def get_user_by_email(db: Session, email: str) -> models.User:
    """ Returns a user's details from the users table according to his email

    :param db:
    :param email:
    :raises UserNotFoundException: In case user_id not in users table
    :return:
    """
    user: models.User = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise UserNotFoundException()
    return user


def get_users_list(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """ Returns a list of all users in the users table

    :param db:
    :param skip:
    :param limit:
    :return:
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: users_schemas.UserCreateBaseModule) -> models.User:
    """ Creates a user in the users table

    :param db:
    :param user:
    :raises EmailAddressAlreadyExistsException: in case there is already an existing user with that email address
    :return: created user details
    """
    is_user_exist: bool = is_user_exist_by_email(db=db, email=user.email)
    if is_user_exist:
        raise EmailAddressAlreadyExistsException()

    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def edit_user(db: Session, user: users_schemas.UserUpdateBaseModule) -> models.User:
    """ Edits an existing user in the users table
    Will updated only fields (email, password, is_active) with a given value, fields with null value will not be updated

    :param db:
    :param user:
    :raises UserNotFoundException: In case user_id doesn't exist in users table
    :raises EmailAddressAlreadyExistsException: In case a given email address to update is already used by another user
    :raises UserFailedDatabaseUpdateException: In case failed to update the database ( For example, trying to update an
        email with an existing email address of another user - which will make DB except as the email field is unique )
    :return: user's updated details
    """
    fake_hashed_password = user.password + "notreallyhashed"
    db_user: models.User = get_user_by_id(db=db, user_id=user.user_id)

    is_email_address_registered: bool = is_user_exist_by_email(db=db, email=user.email)
    if is_email_address_registered:
        raise EmailAddressAlreadyExistsException()

    if user.email is not None:
        db_user.email = user.email
    if user.is_active is not None:
        db_user.is_active = user.is_active
    if user.password is not None:
        db_user.hashed_password = fake_hashed_password

    try:
        db.flush()
        db.commit()
    except sqlalchemy_exceptions.IntegrityError:
        db.rollback()
        raise UserFailedDatabaseUpdateException()
    return db_user


def delete_user(db: Session, user: users_schemas.UserIdBaseModal) -> models.User:
    """ Deletes a user from the users table

    :param db:
    :param user:
    :raises UserNotFoundException: In case user_id not in users table
    :return: deleted user's details
    """
    user: models.User = get_user_by_id(db=db, user_id=user.user_id)
    db.delete(user)
    db.commit()
    return user


def is_user_exist_by_id(db: Session, user_id: users_schemas.UserIdBaseModal) -> bool:
    """ Checks if a user exist in the DB according to user ID

    :param db:
    :param user_id:
    :return: boolean
    """
    try:
        get_user_by_id(db=db, user_id=user_id.user_id)
        return True
    except UserNotFoundException:
        return False


def is_user_exist_by_email(db: Session, email: str) -> bool:
    """ Checks if a user exist in the DB according to email

    :param db:
    :param email:
    :return: boolean
    """
    try:
        get_user_by_email(db=db, email=email)
        return True
    except UserNotFoundException:
        return False
