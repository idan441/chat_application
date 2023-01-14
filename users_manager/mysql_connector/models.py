from sqlalchemy import Boolean, Column, Integer, String

from .database import Base


"""
Defines the tables for the database using SQLAlchemy Base class
"""


class User(Base):
    """ Defines users table """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    salt = Column(String)
    is_active = Column(Boolean, default=True)
