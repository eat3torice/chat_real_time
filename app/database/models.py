from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.orm import relationship
from .connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(Text, nullable=False, unique=True, index=True)
    email = Column(Text, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # relationships
    sent_friend_requests = relationship("Friendship", back_populates="requester", foreign_keys="Friendship.requester_id")
    received_friend_requests = relationship("Friendship", back_populates="receiver", foreign_keys="Friendship.receiver_id")
    conversation_memberships = relationship("ConversationMember", back_populates="user")
    messages = relationship("Message", back_populates="sender")


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("requester_id", "receiver_id", name="uq_friendship_requester_receiver"),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected')", name="chk_friendship_status"),
        CheckConstraint("requester_id <> receiver_id", name="chk_friendship_no_self"),
    )

    requester = relationship("User", foreign_keys=[requester_id], back_populates="sent_friend_requests")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_friend_requests")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=True)  # tên nhóm (để null nếu là 1-1)
    type = Column(Text, nullable=False, default="direct")  # direct = 1-1, group = nhóm
    created_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('direct', 'group')", name="chk_conversation_type"),
    )

    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False, default="member")  # admin, member
    joined_at = Column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conversation_user"),
        CheckConstraint("role IN ('admin', 'member')", name="chk_conversation_member_role"),
    )

    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User", back_populates="conversation_memberships")


class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), index=True)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")


# =========================
# INDEXES (tối ưu hóa)
# =========================
Index("idx_friendship_status", Friendship.status)
Index("idx_conversation_type", Conversation.type)
Index("idx_message_conversation_id", Message.conversation_id)
Index("idx_message_created_at", Message.created_at)