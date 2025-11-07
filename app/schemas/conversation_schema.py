from pydantic import BaseModel
from typing import List, Optional

class ConversationCreate(BaseModel):
    name: Optional[str] = None
    type: str = "direct"  # "direct" or "group"
    member_user_ids: Optional[List[int]] = []

class ConversationOut(BaseModel):
    id: int
    name: Optional[str]
    type: str
    private_pair_key: Optional[str] = None
    member_ids: List[int]

    class Config:
        from_attributes = True