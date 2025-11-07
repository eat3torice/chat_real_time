from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class FriendRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    message: Optional[str]


class FriendResponse(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str

    class Config:
        from_attributes = True


class FriendOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_online: bool = False


class FriendRequestOut(BaseModel):
    id: int
    requester: Dict[str, Any]  # User info
    created_at: datetime
    status: str
