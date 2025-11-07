#!/usr/bin/env python3
"""
WebSocket Test Client for FastAPI Chat Application
"""
import asyncio
import websockets
import json
import sys

async def test_websocket():
    user_id = input("Enter User ID (default: 1): ").strip() or "1"
    uri = f"ws://127.0.0.1:8000/ws/{user_id}"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected as User {user_id}")
            print("Type messages (or 'quit' to exit):")
            
            # Send a test message
            test_message = "Hello WebSocket!"
            await websocket.send(test_message)
            print(f"📤 Sent: {test_message}")
            
            # Listen for responses
            while True:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"📥 Received: {message}")
                except asyncio.TimeoutError:
                    pass
                
                # Check for user input (non-blocking)
                try:
                    user_input = input("Enter message: ").strip()
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    if user_input:
                        await websocket.send(user_input)
                        print(f"📤 Sent: {user_input}")
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                    
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the FastAPI server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("👋 Disconnected")

if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")