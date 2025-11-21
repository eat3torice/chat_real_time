"""
FastAPI application entrypoint for chat_real_time.

This file:
- Registers HTTP routers (auth, messages, groups)
- Registers WebSocket APIRouter (direct + group endpoints)
- Starts/stops the WebSocket ConnectionManager (Redis pub/sub) on app lifecycle events
- Optionally creates DB tables in development when CREATE_DB_ON_STARTUP is enabled
"""
import logging
import os
import json
from typing import Dict, Set
from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings

# Ensure models are imported so SQLAlchemy metadata is populated
from app.database import models  # noqa: F401
from app.websocket_manager import websocket_manager

# Routers (adjust imports if your package layout differs)
from app.routers import auth_router

try:
    from app.routers import conversation_router
except Exception:
    conversation_router = None
try:
    from app.routers import message_router
except Exception:
    message_router = None
try:
    from app.routers import friendship_router
except Exception:
    friendship_router = None
try:
    from app.routers import user_router
except Exception:
    user_router = None

# WebSocket router + manager (OLD - DISABLED TO AVOID CONFLICT)
# If your module path is different (e.g., app.chat.websocket), update the import.
try:
    # DISABLED OLD WEBSOCKET ROUTER TO AVOID CONFLICT WITH NEW ENDPOINT
    # from app.websocket.chat_ws import router as ws_router
    ws_router = None
    ws_manager = None  # Simplified for now
    print("Old WebSocket router DISABLED - using new endpoint in main.py")
except Exception as e:
    print(f"Failed to import WebSocket router: {e}")
    ws_router = None
    ws_manager = None

logger = logging.getLogger("app.main")

app = FastAPI(title="chat_real_time")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.onrender.com",  # Render domains
        "*",  # Remove this in production for security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include registered routers if present
app.include_router(auth_router.router)

if conversation_router is not None:
    app.include_router(conversation_router.router)
else:
    logger.debug("conversation_router not found; skipping include")

if message_router is not None:
    app.include_router(message_router.router)
else:
    logger.debug("message_router not found; skipping include")

if friendship_router is not None:
    app.include_router(friendship_router.router)
else:
    logger.debug("friendship_router not found; skipping include")

if user_router is not None:
    app.include_router(user_router.router)
else:
    logger.debug("user_router not found; skipping include")

if ws_router is not None:
    # WebSocket endpoints are provided by an APIRouter named `router`
    app.include_router(ws_router)
else:
    logger.debug("ws_router not found; WebSocket endpoints not registered")

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# Serve frontend
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


# Serve test realtime page
@app.get("/test_realtime.html")
async def serve_test_realtime():
    return FileResponse("test_realtime.html")


# Serve manual WebSocket test page - UPDATED
@app.get("/manual_ws_test.html")
async def serve_manual_ws_test():
    return FileResponse("manual_ws_test.html")


# Simple WebSocket endpoint for chat with enhanced logging - UPDATED
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    print(f"🔌 WebSocket connection attempt with token: {token[:20]}...")

    # Simple token verification - extract user_id
    user_id = None
    try:
        from app.auth.jwt_handler import decode_access_token

        payload = decode_access_token(token)
        user_id = payload.get("id") or payload.get("user_id")
        print(f"✅ Token verified for user_id: {user_id}")
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    if not user_id:
        print("❌ No user_id found in token")
        await websocket.close(code=4001, reason="Invalid token")
        return

    try:
        await websocket.accept()
        print(f"✅ WebSocket accepted for user {user_id}")
        await websocket_manager.connect(user_id, websocket)
        print(f"✅ User {user_id} registered in WebSocket manager")

        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {"type": "connected", "message": "WebSocket connected successfully"}
            )
        )

        while True:
            data = await websocket.receive_text()
            print(f"📩 Received WebSocket data from user {user_id}: {data}")

            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")

                if message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    print("📤 Sent pong response")
                elif message_type == "join_conversation":
                    conversation_id = message_data.get("conversation_id")
                    if conversation_id:
                        try:
                            print(
                                f"🔧 Processing join_conversation for user {user_id}, conversation {conversation_id}"
                            )
                            await websocket_manager.join_conversation(
                                user_id, conversation_id
                            )
                            print(
                                f"✅ User {user_id} joined conversation {conversation_id}"
                            )
                            # Send confirmation
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "joined_conversation",
                                        "conversation_id": conversation_id,
                                    }
                                )
                            )
                            print(f"📤 Sent joined_conversation confirmation")
                        except Exception as e:
                            print(f"❌ Error joining conversation: {e}")
                            import traceback

                            traceback.print_exc()
                    else:
                        print(f"❌ No conversation_id in join_conversation message")

            except json.JSONDecodeError:
                print("❌ Invalid JSON received")

    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for user {user_id}")
        await websocket_manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"❌ WebSocket error for user {user_id}: {e}")
        import traceback

        traceback.print_exc()
        await websocket_manager.disconnect(user_id, websocket)


@app.on_event("startup")
async def on_startup():
    # Optionally create DB tables in development (use Alembic in production)
    try:
        if str(settings.CREATE_DB_ON_STARTUP).lower() in ("1", "true", "yes"):
            from app.database.connection import engine, Base

            Base.metadata.create_all(bind=engine)
            logger.info("Created DB tables on startup (CREATE_DB_ON_STARTUP=True)")
    except Exception:
        logger.exception("Failed to create DB tables on startup")

    # Start ConnectionManager (connect to Redis and subscribe) if available
    if ws_manager is not None:
        try:
            await ws_manager.start()
            logger.info("WebSocket ConnectionManager started")
        except Exception:
            logger.exception(
                "Failed to start WebSocket ConnectionManager; continuing without it"
            )
    else:
        logger.debug("ws_manager not available; skipping start")


@app.on_event("shutdown")
async def on_shutdown():
    # Stop ConnectionManager gracefully if available
    if ws_manager is not None:
        try:
            await ws_manager.stop()
            logger.info("WebSocket ConnectionManager stopped")
        except Exception:
            logger.exception("Error while stopping WebSocket ConnectionManager")
    else:
        logger.debug("ws_manager not available; skipping stop")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "chat_real_time running"}
