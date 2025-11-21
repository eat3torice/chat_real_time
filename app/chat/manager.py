import asyncio
import json
import logging
from typing import Dict, Set, Optional
from collections import defaultdict
import os

try:
    import redis.asyncio as redis_async
except Exception:
    redis_async = None

logger = logging.getLogger("chat.manager")


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[int, Set] = defaultdict(set)
        self._conversation_members: Dict[int, Set[int]] = defaultdict(
            set
        )  # conversation_id -> user_ids
        self._user_conversations: Dict[int, Set[int]] = defaultdict(
            set
        )  # user_id -> conversation_ids
        self._pub_channel = os.getenv("REDIS_PUBSUB_CHANNEL", "chat_events")
        self._redis_url = os.getenv("REDIS_URL")
        self._redis: Optional[object] = None  # redis.asyncio.Redis
        self._sub_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def connect(self, user_id: int, websocket):
        self._connections[int(user_id)].add(websocket)

    async def disconnect(self, user_id: int, websocket):
        conns = self._connections.get(int(user_id))
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self._connections.pop(int(user_id), None)
            # Clean up conversation memberships for disconnected user
            for conv_id in list(self._user_conversations.get(int(user_id), set())):
                await self.leave_conversation(user_id, conv_id)

    async def join_conversation(self, user_id: int, conversation_id: int):
        """Add user to a conversation room"""
        user_id = int(user_id)
        conversation_id = int(conversation_id)
        self._conversation_members[conversation_id].add(user_id)
        self._user_conversations[user_id].add(conversation_id)

    async def leave_conversation(self, user_id: int, conversation_id: int):
        """Remove user from a conversation room"""
        user_id = int(user_id)
        conversation_id = int(conversation_id)
        self._conversation_members[conversation_id].discard(user_id)
        self._user_conversations[user_id].discard(conversation_id)

        # Clean up empty conversation rooms
        if not self._conversation_members[conversation_id]:
            self._conversation_members.pop(conversation_id, None)

    async def send_to_conversation(self, conversation_id: int, message: dict):
        """Send message to all users in a conversation"""
        conversation_id = int(conversation_id)
        user_ids = self._conversation_members.get(conversation_id, set())
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def send_to_user(self, user_id: int, message: dict):
        conns = list(self._connections.get(int(user_id), set()))
        if not conns:
            return
        payload = json.dumps(message)
        for ws in conns:
            try:
                await ws.send_text(payload)
            except Exception:
                try:
                    await ws.close()
                except Exception:
                    pass
                await self.disconnect(user_id, ws)

    async def publish_event(self, event: dict, target_user_ids: Set[int]):
        for uid in set(target_user_ids):
            await self.send_to_user(uid, event)
        if not self._redis:
            return
        try:
            payload = json.dumps({"event": event, "targets": list(target_user_ids)})
            await self._redis.publish(self._pub_channel, payload)
        except Exception:
            logger.exception("failed to publish to redis")

    async def start(self):
        # start redis subscriber task if redis is configured
        if not self._redis_url or redis_async is None:
            logger.warning(
                "Redis not configured or redis.asyncio not installed; start() is no-op"
            )
            return
        if self._sub_task and not self._sub_task.done():
            return
        try:
            self._redis = redis_async.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
        except Exception:
            logger.exception("Failed to connect to Redis for pub/sub")
            self._redis = None
            return
        loop = asyncio.get_running_loop()
        self._sub_task = loop.create_task(self._subscriber_loop())

    async def stop(self):
        self._shutdown = True
        if self._sub_task:
            self._sub_task.cancel()
            try:
                await self._sub_task
            except asyncio.CancelledError:
                pass
            self._sub_task = None
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                logger.exception("error closing redis")
            self._redis = None

    async def _subscriber_loop(self):
        if not self._redis:
            return
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self._pub_channel)
        try:
            async for message in pubsub.listen():
                if message is None:
                    continue
                if message.get("type") != "message":
                    continue
                data = message.get("data")
                if not data:
                    continue
                try:
                    parsed = json.loads(data)
                except Exception:
                    continue
                event = parsed.get("event")
                targets = parsed.get("targets", [])
                if not event or not targets:
                    continue
                for uid in set(targets):
                    await self.send_to_user(uid, event)
                if self._shutdown:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await pubsub.unsubscribe(self._pub_channel)
            except Exception:
                pass


# singleton instance used by other modules
manager = ConnectionManager()
