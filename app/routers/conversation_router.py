from typing import Any, Dict, List
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Body, Path
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.dependencies import get_current_user
from app.database.models import User, Conversation, ConversationMember, Message
from app.schemas.conversation_schema import ConversationCreate, ConversationOut
from app.chat.services import (
    create_group,
    add_member_to_group,
    remove_member_from_group,
    get_group_info,
    get_conversation_member_ids,
)
from app.chat.manager import manager

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationOut])
def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Any:
    """
    Get all conversations for current user
    """
    conversations = db.query(Conversation).join(ConversationMember).filter(
        ConversationMember.user_id == current_user.id
    ).all()
    
    result = []
    for conv in conversations:
        # Get member IDs for each conversation
        member_ids = get_conversation_member_ids(db, conv.id)
        
        result.append(ConversationOut(
            id=conv.id,
            name=conv.name,
            type=conv.type,
            private_pair_key=getattr(conv, 'private_pair_key', None),
            member_ids=member_ids
        ))
    
    return result


@router.get("/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific conversation by ID
    """
    # Check if user is member of this conversation
    conversation = db.query(Conversation).join(ConversationMember).filter(
        Conversation.id == conversation_id,
        ConversationMember.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get member IDs for this conversation
    member_ids = get_conversation_member_ids(db, conversation.id)
    
    return ConversationOut(
        id=conversation.id,
        name=conversation.name,
        type=conversation.type,
        private_pair_key=getattr(conversation, 'private_pair_key', None),
        member_ids=member_ids
    )


@router.post("", response_model=ConversationOut)
def create_conversation(
    conversation_data: ConversationCreate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new conversation (direct or group)
    """
    try:
        if conversation_data.type == "direct":
            # Direct conversation with one other user
            if not conversation_data.member_user_ids or len(conversation_data.member_user_ids) != 1:
                raise HTTPException(
                    status_code=400, 
                    detail="Direct conversation requires exactly one other user ID"
                )
            
            other_user_id = conversation_data.member_user_ids[0]
            
            # Check if other user exists
            other_user = db.query(User).filter(User.id == other_user_id).first()
            if not other_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Create new direct conversation (don't check for existing for now)
            conversation = Conversation(
                name=None,  # Direct conversations don't have names
                type="direct"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # Add both users as members
            member1 = ConversationMember(
                conversation_id=conversation.id,
                user_id=current_user.id,
                role="member"
            )
            member2 = ConversationMember(
                conversation_id=conversation.id,
                user_id=other_user_id,
                role="member"
            )
            
            db.add(member1)
            db.add(member2)
            db.commit()
            
            member_ids = [current_user.id, other_user_id]
            return ConversationOut(
                id=conversation.id,
                name=conversation.name,
                type=conversation.type,
                private_pair_key=None,
                member_ids=member_ids
            )
        
        else:
            # Group conversation - use existing logic
            conv = create_group(db, current_user.id, conversation_data.name or "Group", conversation_data.member_user_ids or [])
            member_ids = get_conversation_member_ids(db, conv.id)
            return ConversationOut(
                id=conv.id,
                name=conv.name,
                type=conv.type,
                private_pair_key=getattr(conv, 'private_pair_key', None),
                member_ids=member_ids
            )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.post("/groups", response_model=ConversationOut)
def create_group_endpoint(payload: ConversationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Any:
    """
    Create a group conversation. Payload: { "name": "My group", "member_user_ids": [2,3] }.
    Creator becomes admin.
    """
    try:
        creator_id = current_user.id
        
        # Create conversation
        conversation = Conversation(
            name=payload.name or "Group",
            type="group"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Add creator as admin
        creator_member = ConversationMember(
            conversation_id=conversation.id,
            user_id=creator_id,
            role="admin"
        )
        db.add(creator_member)
        
        # Add initial members
        members = [creator_member]
        if payload.member_user_ids:
            for user_id in payload.member_user_ids:
                if user_id != creator_id:  # Don't add creator twice
                    member = ConversationMember(
                        conversation_id=conversation.id,
                        user_id=user_id,
                        role="member"
                    )
                    members.append(member)
                    db.add(member)
        
        db.commit()
        
        # Get member IDs
        member_ids = [m.user_id for m in members]
        
        return ConversationOut(
            id=conversation.id, 
            name=conversation.name, 
            type=conversation.type, 
            private_pair_key=None, 
            member_ids=member_ids
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.delete("/{group_id}/leave", response_model=Dict[str, Any])
def leave_group_endpoint(group_id: int = Path(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Any:
    """
    Current user leaves the group. If user not member -> 404.
    """
    user = current_user
    user_id = int(user.id) if hasattr(user, "id") else int(user.get("id"))
    removed = remove_member_from_group(db, group_id, user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not a group member")
    # notify remaining members
    try:
        member_ids = get_conversation_member_ids(db, group_id)
        event = {"type": "group.member.left", "group_id": group_id, "user_id": user_id}
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(manager.publish_event(event, set(member_ids)))
        except RuntimeError:
            asyncio.run(manager.publish_event(event, set(member_ids)))
    except Exception:
        pass
    return {"status": "ok"}


@router.put("/{conversation_id}/transfer-admin", response_model=Dict[str, Any])
def transfer_admin_endpoint(
    conversation_id: int = Path(...),
    payload: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Transfer admin role to another member. Only current admin can do this.
    """
    try:
        new_admin_id = payload.get("new_admin_id")
        if not new_admin_id:
            raise HTTPException(status_code=400, detail="new_admin_id is required")
        # Check if current user is admin of this conversation
        current_member = db.query(ConversationMember).filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == current_user.id
        ).first()
        
        if not current_member or current_member.role != "admin":
            raise HTTPException(status_code=403, detail="Only conversation admin can transfer admin role")
        
        # Check if conversation is a group
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation or conversation.type != "group":
            raise HTTPException(status_code=400, detail="Can only transfer admin in group conversations")
        
        # Check if new admin is a member
        new_admin_member = db.query(ConversationMember).filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == new_admin_id
        ).first()
        
        if not new_admin_member:
            raise HTTPException(status_code=404, detail="New admin is not a member of this conversation")
        
        # Transfer admin role
        current_member.role = "member"
        new_admin_member.role = "admin"
        db.commit()
        
        # Get new admin user info
        new_admin_user = db.query(User).filter(User.id == new_admin_id).first()
        
        # Send system message about admin transfer
        system_message = Message(
            conversation_id=conversation_id,
            sender_id=None,  # System message
            content=f"{current_user.username} đã chuyển quyền admin cho {new_admin_user.username}"
        )
        db.add(system_message)
        db.commit()
        db.refresh(system_message)
        
        # Notify all members via WebSocket
        try:
            member_ids = get_conversation_member_ids(db, conversation_id)
            event = {
                "type": "conversation.admin_transferred",
                "conversation_id": conversation_id,
                "old_admin_id": current_user.id,
                "new_admin_id": new_admin_id,
                "message": {
                    "id": system_message.id,
                    "content": system_message.content,
                    "sender_id": None,
                    "sender_username": "System",
                    "created_at": system_message.created_at.isoformat()
                }
            }
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(manager.publish_event(event, set(member_ids)))
            except RuntimeError:
                asyncio.run(manager.publish_event(event, set(member_ids)))
        except Exception as e:
            print(f"Failed to send admin transfer notification: {e}")
        
        return {
            "status": "success",
            "message": f"Đã chuyển quyền admin cho {new_admin_user.username}",
            "new_admin": {
                "id": new_admin_user.id,
                "username": new_admin_user.username,
                "email": new_admin_user.email
            }
        }
        
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to transfer admin: {str(e)}")


@router.put("/{conversation_id}", response_model=ConversationOut)
def update_conversation(
    conversation_id: int,
    name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update conversation name
    """
    # Check if user is member of this conversation
    member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    
    # Get the conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update name
    conversation.name = name
    db.commit()
    db.refresh(conversation)
    
    # Get member IDs for response
    member_ids = get_conversation_member_ids(db, conversation.id)
    
    # Notify other members about the change
    try:
        update_event = {
            "type": "conversation_updated",
            "conversation": {
                "id": conversation.id,
                "name": conversation.name,
                "type": conversation.type
            }
        }
        
        # Send to all conversation members
        from app.websocket_manager import websocket_manager
        
        async def notify_members():
            for member_id in member_ids:
                if member_id in websocket_manager.connections:
                    await websocket_manager.send_to_user(member_id, update_event)
        
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(notify_members())
        except RuntimeError:
            asyncio.run(notify_members())
            
    except Exception as e:
        print(f"Error notifying conversation update: {e}")
    
    return ConversationOut(
        id=conversation.id,
        name=conversation.name,
        type=conversation.type,
        private_pair_key=getattr(conversation, 'private_pair_key', None),
        member_ids=member_ids
    )


@router.get("/{conversation_id}/members")
def get_conversation_members(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed information about conversation members
    """
    # Check if user is member of this conversation
    member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    
    # Get all members with user details
    members = db.query(ConversationMember, User).join(User).filter(
        ConversationMember.conversation_id == conversation_id
    ).all()
    
    result = []
    for member, user in members:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": member.role,
            "is_owner": member.role == "admin"
        })
    
    return result


@router.delete("/{conversation_id}/members/{member_id}")
def kick_member(
    conversation_id: int,
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Kick a member from conversation (only admin/owner can do this)
    """
    # Check if current user is admin of this conversation
    current_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    ).first()
    
    if not current_member or current_member.role != "admin":
        raise HTTPException(status_code=403, detail="Only conversation admin can kick members")
    
    # Check if target member exists
    target_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == member_id
    ).first()
    
    if not target_member:
        raise HTTPException(status_code=404, detail="Member not found in this conversation")
    
    # Cannot kick yourself
    if member_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot kick yourself")
    
    # Get member username for notification
    kicked_user = db.query(User).filter(User.id == member_id).first()
    
    # Remove member
    db.delete(target_member)
    db.commit()
    
    # Notify all remaining members
    try:
        from app.websocket_manager import websocket_manager
        
        # Get remaining member IDs
        remaining_members = db.query(ConversationMember).filter(
            ConversationMember.conversation_id == conversation_id
        ).all()
        member_ids = [m.user_id for m in remaining_members]
        
        # Create notification event
        event = {
            "type": "member_kicked",
            "conversation_id": conversation_id,
            "kicked_user": {
                "id": member_id,
                "username": kicked_user.username if kicked_user else "Unknown"
            },
            "kicked_by": {
                "id": current_user.id,
                "username": current_user.username
            }
        }
        
        async def notify_members():
            for mid in member_ids:
                if mid in websocket_manager.connections:
                    await websocket_manager.send_to_user(mid, event)
            
            # Also notify the kicked user
            if member_id in websocket_manager.connections:
                await websocket_manager.send_to_user(member_id, {
                    "type": "kicked_from_conversation",
                    "conversation_id": conversation_id,
                    "message": f"Bạn đã bị loại khỏi cuộc trò chuyện bởi {current_user.username}"
                })
        
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(notify_members())
        except RuntimeError:
            asyncio.run(notify_members())
            
    except Exception as e:
        print(f"Error notifying member kick: {e}")
    
    return {"status": "success", "message": f"Đã loại {kicked_user.username if kicked_user else 'thành viên'} khỏi cuộc trò chuyện"}


@router.post("/{conversation_id}/members")
def add_member_to_conversation(
    conversation_id: int,
    user_id: int = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Add a member to conversation (admin only or based on conversation settings)
    """
    # Check if current user is member of this conversation
    current_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    ).first()
    
    if not current_member:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    
    # Get conversation settings
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Direct conversations cannot have additional members
    if conversation.type == "direct":
        raise HTTPException(status_code=403, detail="Cannot add members to direct conversations")
    
    # Check permissions based on conversation type and settings
    conversation_settings = getattr(conversation, 'settings', {}) or {}
    allow_member_add = conversation_settings.get('allow_member_add', False)
    
    # Only admin can add members, unless conversation allows it
    if not allow_member_add and current_member.role != "admin":
        raise HTTPException(status_code=403, detail="Only conversation admin can add members")
    
    # Check if user to add exists
    new_user = db.query(User).filter(User.id == user_id).first()
    if not new_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is already a member
    existing_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user_id
    ).first()
    
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    # Add new member
    new_member = ConversationMember(
        conversation_id=conversation_id,
        user_id=user_id,
        role="member"
    )
    db.add(new_member)
    db.commit()
    
    # Notify all members
    try:
        from app.websocket_manager import websocket_manager
        
        # Get all member IDs including the new one
        all_members = db.query(ConversationMember).filter(
            ConversationMember.conversation_id == conversation_id
        ).all()
        member_ids = [m.user_id for m in all_members]
        
        # Create notification event
        event = {
            "type": "member_added",
            "conversation_id": conversation_id,
            "new_user": {
                "id": user_id,
                "username": new_user.username
            },
            "added_by": {
                "id": current_user.id,
                "username": current_user.username
            }
        }
        
        async def notify_members():
            for mid in member_ids:
                if mid in websocket_manager.connections:
                    await websocket_manager.send_to_user(mid, event)
        
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(notify_members())
        except RuntimeError:
            asyncio.run(notify_members())
            
    except Exception as e:
        print(f"Error notifying member add: {e}")
    
    return {
        "status": "success", 
        "message": f"Đã thêm {new_user.username} vào cuộc trò chuyện",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }


@router.put("/{conversation_id}/settings")
def update_conversation_settings(
    conversation_id: int,
    settings: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update conversation settings (admin only)
    """
    # Check if current user is admin of this conversation
    current_member = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == current_user.id
    ).first()
    
    if not current_member or current_member.role != "admin":
        raise HTTPException(status_code=403, detail="Only conversation admin can update settings")
    
    # Get the conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update settings (store as JSON in a settings column or use a separate table)
    # For now, we'll assume conversation model has a settings JSON field
    conversation.settings = settings
    db.commit()
    
    return {"status": "success", "message": "Đã cập nhật cài đặt cuộc trò chuyện", "settings": settings}