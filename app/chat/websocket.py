# append the group websocket handler to your existing chatbot websocket file
import json
import logging
from typing import Optional

from fastapi import WebSocket, Query, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_optional
from app.database.connection import SessionLocal
from app.chat.services import (
    get_conversation_member_ids,
    create_message,
)
from app.chat.manager import manager
from app.chat.utils import build_message_event, build_error_event

logger = logging.getLogger("chat.websocket")


async def ws_group_handler(websocket: WebSocket, group_id: int, token: Optional[str] = Query(None)):
    """
    WebSocket handler for group chat.
    Connect: ws://host/ws/group/{group_id}?token=<JWT>
    """
    # authenticate token (non-raising)
    user_payload = get_current_user_optional(token)
    if not user_payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id = int(user_payload.get("id"))

    # verify membership before accepting
    db: Session = SessionLocal()
    try:
        member_ids = await run_in_threadpool(get_conversation_member_ids, db, group_id)
        if user_id not in member_ids:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        db.close()

    await websocket.accept()
    await manager.connect(user_id, websocket)
    logger.info("ws group connected user=%s group=%s", user_id, group_id)

    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                await websocket.send_json(build_error_event("invalid json"))
                continue

            typ = data.get("type")
            if typ == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if typ == "message.create":
                content = data.get("content")
                if content is None:
                    await websocket.send_json(build_error_event("content required"))
                    continue

                # persist message
                db: Session = SessionLocal()
                try:
                    member_ids = await run_in_threadpool(get_conversation_member_ids, db, group_id)
                    if user_id not in member_ids:
                        await websocket.send_json(build_error_event("not a group member"))
                        continue
                    msg = await run_in_threadpool(create_message, db, group_id, user_id, content)
                finally:
                    db.close()

                event = build_message_event(msg)
                await manager.publish_event(event, set(member_ids))
                continue

            await websocket.send_json(build_error_event("unknown type"))
    except Exception as exc:
        logger.exception("ws group loop error: %s", exc)
    finally:
        await manager.disconnect(user_id, websocket)