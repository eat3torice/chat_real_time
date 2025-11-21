from typing import Any, Set, List
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.message_schema import MessageCreate, MessageOut
from app.chat.services import (
    get_or_create_direct_conversation,
    create_message,
    get_conversation_member_ids,
)
from app.dependencies.use_loader import get_user_by_token
from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.database.models import Message, Conversation, ConversationMember, User
from app.chat.manager import manager
from app.chat.utils import build_message_event

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/conversation/{conversation_id}", response_model=List[MessageOut])
def get_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get messages for a conversation with pagination
    """
    # Verify user is member of this conversation
    member = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == current_user.id,
        )
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404, detail="Conversation not found or access denied"
        )

    # Get messages for this conversation
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Convert to MessageOut format
    result = []
    for msg in messages:
        # Get sender info
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        result.append(
            MessageOut(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender_id=msg.sender_id,
                sender_username=sender.username if sender else "Unknown",
                content=msg.content,
                created_at=msg.created_at,
            )
        )

    # Return in chronological order (oldest first)
    return list(reversed(result))


@router.post("", response_model=MessageOut)
async def send_message_to_conversation(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Send a message to a conversation
    """
    if not payload.conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    # Verify user is member of this conversation
    member = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == payload.conversation_id,
            ConversationMember.user_id == current_user.id,
        )
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404, detail="Conversation not found or access denied"
        )

    try:
        # Create the message
        msg_dict = create_message(
            db, payload.conversation_id, current_user.id, payload.content
        )

        # Convert created_at to string if it's datetime
        created_at = msg_dict["created_at"]
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()

        # Send real-time notification to conversation members
        message_event = {
            "type": "new_message",
            "message": {
                "id": msg_dict["id"],
                "conversation_id": msg_dict["conversation_id"],
                "sender_id": msg_dict["sender_id"],
                "sender_username": current_user.username,
                "content": msg_dict["content"],
                "created_at": created_at,
            },
        }

        # Import and use the global WebSocket manager
        try:
            from app.websocket_manager import websocket_manager

            await websocket_manager.send_to_conversation(
                payload.conversation_id, message_event
            )
            print(f"✅ Broadcasted message to conversation {payload.conversation_id}")
        except Exception as e:
            print(f"❌ WebSocket broadcast error: {e}")
            import traceback

            traceback.print_exc()

        return MessageOut(
            id=msg_dict["id"],
            conversation_id=msg_dict["conversation_id"],
            sender_id=msg_dict["sender_id"],
            sender_username=current_user.username,
            content=msg_dict["content"],
            created_at=created_at,
        )
    except Exception as e:
        print(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to create message")


@router.post("/send", response_model=MessageOut)
def send_message(
    payload: MessageCreate,
    current_user=Depends(get_user_by_token),
    db: Session = Depends(get_db),
) -> Any:
    """
    Legacy endpoint for direct messaging (kept for backward compatibility)
    """
    sender = current_user
    sender_id = int(sender.id) if hasattr(sender, "id") else int(sender.get("id"))
    receiver_id = int(payload.receiver_id)

    conv = get_or_create_direct_conversation(db, sender_id, receiver_id)
    msg = create_message(db, conv.id, sender_id, payload.content)
    member_ids = get_conversation_member_ids(db, conv.id)
    target_ids: Set[int] = set(member_ids)

    # publish in background (do not block response)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.publish_event(build_message_event(msg), target_ids))
    except RuntimeError:
        asyncio.run(manager.publish_event(build_message_event(msg), target_ids))

    return msg
