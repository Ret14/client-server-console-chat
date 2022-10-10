from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)

    user_id_messages = relationship(
        "Messages",
        back_populates="parent",
        cascade="all, delete",
        passive_deletes=True,
    )
    # user_id_private_messages = relationship(
    #     "PrivateMessages",
    #     back_populates="parent",
    #     cascade="all, delete",
    #     passive_deletes=True,
    # )


class Messages(Base):
    __tablename__ = 'messages'
    __table_args__ = {'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    text = Column(String(100), nullable=False)

    parent = relationship("Users", back_populates="user_id_messages")


class PrivateMessages(Base):
    __tablename__ = 'private_messages'
    __table_args__ = {'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    target_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    text = Column(String(100), nullable=False)

    sender = relationship("Users", foreign_keys=[sender_id])
    target = relationship("Users", foreign_keys=[target_id])
