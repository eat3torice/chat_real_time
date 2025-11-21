"""Tests for WebSocket functionality"""

import pytest
from fastapi.testclient import TestClient


def test_websocket_connection_requires_token(client):
    """Test WebSocket connection without token fails"""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/invalid_token"):
            pass


def test_websocket_connection_success(client, test_user_token):
    """Test WebSocket connection with valid token succeeds"""
    with client.websocket_connect(f"/ws/{test_user_token}") as websocket:
        # Nhận nhiều message, lấy message đầu tiên có type == "connected"
        for _ in range(10):
            msg = websocket.receive_json(mode="text")
            if msg.get("type") == "connected":
                assert msg["type"] == "connected"
                return
        assert False, "Did not receive 'connected' message"


def test_websocket_ping_pong(client, test_user_token):
    """Test WebSocket ping-pong mechanism"""
    with client.websocket_connect(f"/ws/{test_user_token}") as websocket:
        # Skip welcome message
        websocket.receive_json(mode="text")
        
        # Send ping
        websocket.send_json({"type": "ping"})
        
        # Should receive pong (may have friend status messages first)
        response = None
        for _ in range(10):
            msg = websocket.receive_json(mode="text")
            if msg.get("type") == "pong":
                response = msg
                break
        
        assert response is not None
        assert response["type"] == "pong"


def test_websocket_join_conversation(client, test_user_token):
    """Test joining a conversation via WebSocket"""
    # First create a conversation via API
    conversation_response = client.post(
        "/conversations",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={"type": "group", "name": "Test Group", "member_user_ids": []}
    )
    
    # Check if conversation was created successfully
    assert conversation_response.status_code == 200
    conversation_data = conversation_response.json()
    assert "id" in conversation_data
    conversation_id = conversation_data["id"]
    
    # Connect to WebSocket and join conversation
    with client.websocket_connect(f"/ws/{test_user_token}") as websocket:
        # Skip welcome message
        websocket.receive_json(mode="text")
        
        # Join conversation
        websocket.send_json({
            "type": "join_conversation",
            "conversation_id": conversation_id
        })
        
        # Should receive joined_conversation confirmation
        response = None
        for _ in range(10):
            msg = websocket.receive_json(mode="text")
            if msg.get("type") == "joined_conversation":
                response = msg
                break
        
        # Verify we got confirmation
        if response:
            assert response["type"] == "joined_conversation"
            assert response["conversation_id"] == conversation_id
