from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime

class MessageCreate(BaseModel):
    conversation_id: Optional[int] = None  # For conversation-based messaging
    receiver_id: Optional[int] = None      # For legacy direct messaging
    content: str

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_username: Optional[str] = None
    content: str
    created_at: Union[datetime, str]

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: int
    name: Optional[str]
    type: str
    private_pair_key: Optional[str]
    member_ids: List[int]