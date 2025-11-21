"""
Simple WebSocket Manager for Real-time Chat
"""
import json
from typing import Dict, Set
from collections import defaultdict


class SimpleWebSocketManager:
    def __init__(self):
        self.connections: Dict[int, Set] = defaultdict(set)
        self.conversation_members: Dict[int, Set[int]] = defaultdict(set)

    async def connect(self, user_id: int, websocket):
        was_offline = (
            user_id not in self.connections or len(self.connections[user_id]) == 0
        )
        self.connections[user_id].add(websocket)
        print(f"User {user_id} connected via WebSocket")

        # Send online notification to friends if user was offline
        if was_offline:
            await self.broadcast_user_status(user_id, True)

        # Send current online status of friends to this user
        await self.send_friends_status(user_id)

    async def disconnect(self, user_id: int, websocket):
        self.connections[user_id].discard(websocket)
        is_now_offline = not self.connections[user_id]
        if is_now_offline:
            self.connections.pop(user_id, None)
            # Send offline notification to friends
            await self.broadcast_user_status(user_id, False)
        print(f"User {user_id} disconnected from WebSocket")

    async def broadcast_user_status(self, user_id: int, is_online: bool):
        """Broadcast user online/offline status to their friends"""
        try:
            # Import here to avoid circular imports
            from app.database.connection import get_db
            from app.database.models import User, Friendship
            from sqlalchemy.orm import Session

            # Get database session
            db = next(get_db())

            # Get user's friends
            friendships = (
                db.query(Friendship)
                .filter(
                    Friendship.status == "accepted",
                    (
                        (Friendship.requester_id == user_id)
                        | (Friendship.receiver_id == user_id)
                    ),
                )
                .all()
            )

            friend_ids = []
            for friendship in friendships:
                friend_id = (
                    friendship.receiver_id
                    if friendship.requester_id == user_id
                    else friendship.requester_id
                )
                friend_ids.append(friend_id)

            # Send status update to online friends
            status_message = {
                "type": "user_online" if is_online else "user_offline",
                "user_id": user_id,
            }

            for friend_id in friend_ids:
                if friend_id in self.connections:
                    await self.send_to_user(friend_id, status_message)

            db.close()
            print(
                f"📡 Broadcasted {user_id} status ({'online' if is_online else 'offline'}) to {len(friend_ids)} friends"
            )

        except Exception as e:
            print(f"❌ Error broadcasting user status: {e}")
            import traceback

            traceback.print_exc()

    async def send_friends_status(self, user_id: int):
        """Send current online status of all friends to a newly connected user"""
        try:
            # Import here to avoid circular imports
            from app.database.connection import get_db
            from app.database.models import User, Friendship
            from sqlalchemy.orm import Session

            # Get database session
            db = next(get_db())

            # Get user's friends
            friendships = (
                db.query(Friendship)
                .filter(
                    Friendship.status == "accepted",
                    (
                        (Friendship.requester_id == user_id)
                        | (Friendship.receiver_id == user_id)
                    ),
                )
                .all()
            )

            friend_ids = []
            for friendship in friendships:
                friend_id = (
                    friendship.receiver_id
                    if friendship.requester_id == user_id
                    else friendship.requester_id
                )
                friend_ids.append(friend_id)

            # Send status of each friend
            for friend_id in friend_ids:
                is_online = friend_id in self.connections
                status_message = {
                    "type": "user_online" if is_online else "user_offline",
                    "user_id": friend_id,
                }
                await self.send_to_user(user_id, status_message)

            db.close()
            print(f"📤 Sent status of {len(friend_ids)} friends to user {user_id}")

        except Exception as e:
            print(f"❌ Error sending friends status: {e}")
            import traceback

            traceback.print_exc()

    async def join_conversation(self, user_id: int, conversation_id: int):
        self.conversation_members[conversation_id].add(user_id)
        print(f"User {user_id} joined conversation {conversation_id}")

    async def send_to_conversation(self, conversation_id: int, message: dict):
        """Send message to all users in a conversation"""
        user_ids = self.conversation_members.get(conversation_id, set())
        print(f"🚀 Sending to conversation {conversation_id}")
        print(f"👥 Conversation members: {user_ids}")
        print(f"🌐 All connected users: {list(self.connections.keys())}")
        print(f"📨 Message: {message}")

        if not user_ids:
            print(
                f"❌ No members found for conversation {conversation_id}, broadcasting to all connected users"
            )
            # Broadcast to all connected users for now
            for user_id in self.connections.keys():
                await self.send_to_user(user_id, message)
            return

        print(f"✅ Broadcasting to conversation members: {user_ids}")
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to a specific user"""
        connections = list(self.connections.get(user_id, set()))
        if connections:
            message_text = json.dumps(message)
            sent_count = 0
            for ws in connections:
                try:
                    await ws.send_text(message_text)
                    sent_count += 1
                except Exception as e:
                    print(f"❌ Failed to send to user {user_id}: {e}")
                    await self.disconnect(user_id, ws)

            if sent_count > 0:
                print(
                    f"✅ Sent message to user {user_id}: {message['type']} ({sent_count} connections)"
                )


# Global manager instance
websocket_manager = SimpleWebSocketManager()
