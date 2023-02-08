from sqlalchemy import Boolean, Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


"""
Defines the tables for the database using SQLAlchemy Base class
"""


class User(Base):
    """ Defines users table """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, nullable=True)
    text_status = Column(String, nullable=True)

    # user_sent_messages = relationship("Message", back_populates="sender_id")
    # user_received_messages = relationship("Message", back_populates="receiver_id")


class Message(Base):
    """ Defines users table """
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True)
    message_content = Column(String)
    sender_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    is_message_read = Column(Boolean, default=False, nullable=False)
    sent_datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    received_datetime = Column(DateTime(timezone=True), default=None)

    # sender_user = relationship("User", back_populates="user_id")
    # receiver_user = relationship("User", back_populates="user_id")
