def build_message_event(message: dict) -> dict:
    """
    Build a standard event payload for a newly created message.
    `message` is a serializable dict returned from create_message.
    Returns a dict ready to be sent to websocket clients (will be JSON-encoded).
    """
    return {"type": "message.new", "message": message}


def build_error_event(msg: str) -> dict:
    """
    Build a simple error event payload for sending to clients.
    """
    return {"type": "error", "message": msg}