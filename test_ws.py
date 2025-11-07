import asyncio
import websockets
import json

async def test_websocket():
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect("ws://127.0.0.1:8000/ws-test") as websocket:
            print("Connected successfully!")
            
            # Send test message
            await websocket.send("Hello WebSocket!")
            print("Sent: Hello WebSocket!")
            
            # Receive response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())