from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()


@router.websocket("/ws-test")
async def websocket_test(websocket: WebSocket):
    """
    Simple WebSocket test endpoint
    """
    print("WebSocket test connection attempt")
    await websocket.accept()
    print("WebSocket test connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("WebSocket test disconnected")


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time chat
    Simple version without complex dependencies
    """
    print(f"WebSocket connection attempt with token: {token[:20]}...")

    # For now, accept any token (simplified for testing)
    await websocket.accept()
    print("WebSocket connection accepted")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket data: {data}")

            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")

                if message_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    print("Sent pong response")
                else:
                    # Echo back for now
                    await websocket.send_text(
                        json.dumps({"type": "echo", "data": message_data})
                    )

            except json.JSONDecodeError:
                print("Invalid JSON received")

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
