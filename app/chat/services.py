from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Conversation, ConversationMember, Message, User


def _pair_key_for_users(a: int, b: int) -> str:
    a, b = sorted([int(a), int(b)])
    return f"direct:{a}:{b}"


def get_direct_conversation_between(db: Session, user_a: int, user_b: int) -> Optional[Conversation]:
    pair_key = _pair_key_for_users(user_a, user_b)
    stmt = select(Conversation).where(Conversation.private_pair_key == pair_key, Conversation.type == "direct")
    return db.execute(stmt).scalars().first()


def create_direct_conversation(db: Session, user_a: int, user_b: int) -> Conversation:
    pair_key = _pair_key_for_users(user_a, user_b)
    conv = Conversation(name=None, type="direct", private_pair_key=pair_key)
    db.add(conv)
    db.flush()  # populate conv.id
    m1 = ConversationMember(conversation_id=conv.id, user_id=int(user_a), role="member")
    m2 = ConversationMember(conversation_id=conv.id, user_id=int(user_b), role="member")
    db.add_all([m1, m2])
    db.commit()
    db.refresh(conv)
    return conv


def get_or_create_direct_conversation(db: Session, user_a: int, user_b: int) -> Conversation:
    conv = get_direct_conversation_between(db, user_a, user_b)
    if conv:
        return conv
    return create_direct_conversation(db, user_a, user_b)


def create_message(db: Session, conversation_id: int, sender_id: int, content: str, message_type: str = "text") -> Dict[str, Any]:
    now = datetime.utcnow()
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        created_at=now,
    )
    db.add(msg)
    db.flush()
    db.commit()
    db.refresh(msg)
    return {
        "id": int(msg.id),
        "conversation_id": int(msg.conversation_id),
        "sender_id": int(msg.sender_id) if msg.sender_id is not None else None,
        "content": msg.content,
        "message_type": message_type,  # Keep for compatibility but don't store in DB
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def get_conversation_member_ids(db: Session, conversation_id: int) -> List[int]:
    stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == conversation_id)
    rows = db.execute(stmt).scalars().all()
    return [int(x) for x in rows]


# -----------------------
# Group (conversation type='group') helpers
# -----------------------
def create_group(db: Session, creator_id: int, name: str, initial_member_ids: Optional[List[int]] = None) -> Conversation:
    """
    Create a 'group' Conversation and add creator + initial members.
    Returns Conversation instance.
    """
    conv = Conversation(name=name, type="group", private_pair_key=None)
    db.add(conv)
    db.flush()  # populate conv.id

    members = []
    # add creator as admin
    members.append(ConversationMember(conversation_id=conv.id, user_id=int(creator_id), role="admin"))
    # add initial members as members
    if initial_member_ids:
        for uid in set(initial_member_ids):
            if int(uid) == int(creator_id):
                continue
            members.append(ConversationMember(conversation_id=conv.id, user_id=int(uid), role="member"))
    db.add_all(members)
    db.commit()
    db.refresh(conv)
    return conv


def add_member_to_group(db: Session, conversation_id: int, username_or_email: str) -> Optional[ConversationMember]:
    """
    Find user by username or email and add to conversation as member if not already present.
    Returns ConversationMember or None if user not found or already member.
    """
    user = db.query(User).filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    if not user:
        return None
    # check existing membership
    existing = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user.id
    ).first()
    if existing:
        return existing
    member = ConversationMember(conversation_id=conversation_id, user_id=user.id, role="member")
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member_from_group(db: Session, conversation_id: int, user_id: int) -> bool:
    """
    Remove user from conversation. Returns True if removed, False if not member.
    """
    member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == int(user_id)
    ).first()
    if not member:
        return False
    db.delete(member)
    db.commit()
    return True


def get_group_info(db: Session, conversation_id: int) -> Optional[Dict[str, Any]]:
    conv = db.get(Conversation, int(conversation_id))
    if not conv or conv.type != "group":
        return None
    member_ids = get_conversation_member_ids(db, conv.id)
    return {
        "id": conv.id,
        "name": conv.name,
        "type": conv.type,
        "member_ids": member_ids,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }