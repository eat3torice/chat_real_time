from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.database.models import Conversation, ConversationMember, Message, User


def get_direct_conversation_between(
    db: Session, user_a: int, user_b: int
) -> Optional[Conversation]:
    """
    Return Conversation instance for direct chat between user_a and user_b if exists.
    Assumes a conversation of type 'direct' with exactly those two members can be identified by a private_pair_key.
    We'll use deterministic private_pair_key for direct chats to find existing conversation.
    """
    # create deterministic pair key ordered by id to find same conversation
    a, b = sorted([int(user_a), int(user_b)])
    pair_key = f"direct:{a}:{b}"
    stmt = select(Conversation).where(
        Conversation.private_pair_key == pair_key, Conversation.type == "direct"
    )
    return db.execute(stmt).scalars().first()


def create_direct_conversation(
    db: Session, user_a: int, user_b: int, name: Optional[str] = None
) -> Conversation:
    """
    Create new direct Conversation with deterministic private_pair_key and add both members.
    """
    a, b = sorted([int(user_a), int(user_b)])
    pair_key = f"direct:{a}:{b}"
    conv = Conversation(name=name, type="direct", private_pair_key=pair_key)
    db.add(conv)
    db.flush()  # populate conv.id
    # add members
    m1 = ConversationMember(conversation_id=conv.id, user_id=a, role="member")
    m2 = ConversationMember(conversation_id=conv.id, user_id=b, role="member")
    db.add_all([m1, m2])
    db.commit()
    db.refresh(conv)
    return conv


def create_message(
    db: Session,
    conversation_id: int,
    sender_id: int,
    content: str,
    message_type: str = "text",
) -> Dict[str, Any]:
    """
    Persist a message and return serializable dict.
    """
    now = datetime.utcnow()
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
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
        "message_type": msg.message_type,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def get_conversation_member_ids(db: Session, conversation_id: int) -> List[int]:
    stmt = select(ConversationMember.user_id).where(
        ConversationMember.conversation_id == conversation_id
    )
    rows = db.execute(stmt).scalars().all()
    return [int(x) for x in rows]
