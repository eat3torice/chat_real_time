import asyncio
import websockets
import json

async def test_websocket_client():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MiwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImlhdCI6MTc2MjE1MTI1MCwiZXhwIjoxNzYyMTU0ODUwfQ.Mjz8wn9UakHzvTRlyCGtWEAEYXcUDP5SgAFTdoCM_zo"
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(f"ws://127.0.0.1:8000/ws/{token}") as websocket:
            print("Connected successfully!")
            
            # Join conversation 1
            join_message = {
                "type": "join_conversation",
                "conversation_id": 1
            }
            await websocket.send(json.dumps(join_message))
            print("Sent join_conversation message")
            
            # Listen for messages
            print("Listening for messages...")
            async for message in websocket:
                data = json.loads(message)
                print(f"Received: {data}")
                
                if data.get("type") == "new_message":
                    msg = data.get("message", {})
                    print(f"📨 NEW MESSAGE: {msg.get('content')} (from {msg.get('sender_username')})")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_client())