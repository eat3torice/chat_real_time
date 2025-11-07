from typing import Any


def send_notification(user_id: int, event: str, payload: Any):
    # placeholder: in a real app, you'd publish to websocket manager or push service
    print(f"Notify {user_id}: {event} -> {payload}")
