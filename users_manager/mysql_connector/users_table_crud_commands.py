from sqlalchemy.orm import Session

from . import models
from pydantic_schemas import users_schemas


"""
Defines top-level methods for manipulating data in the users table
"""


def get_user_by_id(db: Session, user_id: int):
    """ Returns a user's details from the users table according to his user ID

    :param db:
    :param user_id:
    :return:
    """
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """ Returns a user's details from the users table according to his email

    :param db:
    :param email:
    :return:
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_users_list(db: Session, skip: int = 0, limit: int = 100):
    """ Returns a list of all users in the users table

    :param db:
    :param skip:
    :param limit:
    :return:
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: users_schemas.UserCreateBaseModule):
    """ Creates a user in the users table

    :param db:
    :param user:
    :return: created user details
    """
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def edit_user(db: Session, user: users_schemas.UserUpdateBaseModule):
    """ Edits an existing user in the users table
    Will updated only fields (email, password, is_active) with a given value, fields with null value will not be updated

    :param db:
    :param user:
    :return: user's updated details
    """
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = db.query(models.User).filter(models.User.user_id == user.user_id).first()

    if user.email is not None:
        db_user.email = user.email
    if user.is_active is not None:
        db_user.is_active = user.is_active
    if user.password is not None:
        db_user.hashed_password = fake_hashed_password

    db.flush()
    db.commit()
    return db_user


def delete_user(db: Session, user: users_schemas.UserIdBaseModal):
    """ Deletes a user from the users table

    :param db:
    :param user:
    :return: deleted user's details
    """
    user: models.User = db.query(models.User).filter(models.User.user_id == user.user_id).first()
    db.delete(user)
    db.commit()
    return user
