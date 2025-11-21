from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.auth.dependencies import get_current_user
from app.database.models import User, Friendship
from app.schemas.friendship_schema import FriendRequestOut, FriendOut

router = APIRouter(prefix="/friends", tags=["friends"])


@router.get("", response_model=List[FriendOut])
def get_friends(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    """
    Get all friends for current user
    """
    # Get accepted friendships where current user is either requester or receiver
    friendships = (
        db.query(Friendship)
        .filter(
            Friendship.status == "accepted",
            (
                (Friendship.requester_id == current_user.id)
                | (Friendship.receiver_id == current_user.id)
            ),
        )
        .all()
    )

    friends = []
    for friendship in friendships:
        # Get the other user (friend)
        friend_id = (
            friendship.receiver_id
            if friendship.requester_id == current_user.id
            else friendship.requester_id
        )
        friend = db.query(User).filter(User.id == friend_id).first()

        if friend:
            # Check if friend is online via WebSocket manager
            try:
                from app.websocket_manager import websocket_manager

                is_online = friend_id in websocket_manager.connections
            except:
                is_online = False

            friends.append(
                FriendOut(
                    id=friend.id,
                    username=friend.username,
                    email=friend.email,
                    is_online=is_online,
                )
            )

    return friends


@router.get("/requests", response_model=List[FriendRequestOut])
def get_friend_requests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Any:
    """
    Get pending friend requests for current user
    """
    requests = (
        db.query(Friendship)
        .filter(
            Friendship.receiver_id == current_user.id, Friendship.status == "pending"
        )
        .all()
    )

    result = []
    for request in requests:
        requester = db.query(User).filter(User.id == request.requester_id).first()
        if requester:
            result.append(
                FriendRequestOut(
                    id=request.id,
                    requester={
                        "id": requester.id,
                        "username": requester.username,
                        "email": requester.email,
                    },
                    created_at=request.created_at,
                    status=request.status,
                )
            )

    return result


@router.post("/request")
def send_friend_request(
    request_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Send friend request to another user
    """
    username = request_data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    # Find target user
    target_user = db.query(User).filter(User.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot send friend request to yourself"
        )

    # Check if friendship already exists
    existing = (
        db.query(Friendship)
        .filter(
            (
                (Friendship.requester_id == current_user.id)
                & (Friendship.receiver_id == target_user.id)
            )
            | (
                (Friendship.requester_id == target_user.id)
                & (Friendship.receiver_id == current_user.id)
            )
        )
        .first()
    )

    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=400, detail="Already friends")
        elif existing.status == "pending":
            raise HTTPException(status_code=400, detail="Friend request already sent")

    # Create friend request
    friendship = Friendship(
        requester_id=current_user.id, receiver_id=target_user.id, status="pending"
    )

    db.add(friendship)
    db.commit()

    return {"message": "Friend request sent successfully"}


@router.put("/requests/{request_id}/accept")
def accept_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Accept a friend request
    """
    request = (
        db.query(Friendship)
        .filter(
            Friendship.id == request_id,
            Friendship.receiver_id == current_user.id,
            Friendship.status == "pending",
        )
        .first()
    )

    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    request.status = "accepted"
    db.commit()

    return {"message": "Friend request accepted"}


@router.put("/requests/{request_id}/reject")
def reject_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Reject a friend request
    """
    request = (
        db.query(Friendship)
        .filter(
            Friendship.id == request_id,
            Friendship.receiver_id == current_user.id,
            Friendship.status == "pending",
        )
        .first()
    )

    if not request:
        raise HTTPException(status_code=404, detail="Friend request not found")

    request.status = "rejected"
    db.commit()

    return {"message": "Friend request rejected"}
