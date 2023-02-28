from typing import Dict, Union
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
    email = Column(Integer, unique=True)
    nickname = Column(String, nullable=True)
    text_status = Column(String, nullable=True)

    # user_sent_messages = relationship("Message", back_populates="sender_id")
    # user_received_messages = relationship("Message", back_populates="receiver_id")

    def json(self) -> Dict:
        """ Returns user details as a dictionary

        :return:
        """
        user_details_dict: Dict[str, any] = {"user_id": self.user_id,
                                             "email": self.email,
                                             "nickname": self.nickname,
                                             "text_status": self.text_status}
        return user_details_dict


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

    def json(self) -> Dict:
        """ Returns message details as a dictionary

        :return:
        """
        message_details_dict: Dict[str, any] = {"message_id": self.message_id,
                                                "message_content": self.message_content,
                                                "sender_id": self.sender_id,
                                                "receiver_id": self.receiver_id,
                                                "is_message_read": self.is_message_read,
                                                "sent_datetime": self.sent_datetime,
                                                "received_datetime": self.received_datetime,
                                                }
        return message_details_dict
