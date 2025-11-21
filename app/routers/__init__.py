from fastapi import APIRouter

api_router = APIRouter()

from . import (
    auth_router,
    user_router,
    conversation_router,
    message_router,
    friendship_router,
)  # noqa

# You can include routers in main.py like:
# api_router.include_router(auth_router.router, prefix="/auth")
