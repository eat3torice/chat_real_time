"""Tests for authentication endpoints"""

import pytest


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_register_success(client, test_user_data):
    """Test successful user registration"""
    response = client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]
    assert "password" not in data
    assert "id" in data


def test_register_duplicate_username(client, test_user_data):
    """Test registration with duplicate username fails"""
    # First registration
    client.post("/auth/register", json=test_user_data)
    
    # Second registration with same username should fail
    response = client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == 400


def test_login_success(client, test_user_data):
    """Test successful login"""
    # Register user first
    client.post("/auth/register", json=test_user_data)
    
    # Login
    response = client.post("/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client, test_user_data):
    """Test login with wrong password fails"""
    # Register user
    client.post("/auth/register", json=test_user_data)
    
    # Try login with wrong password
    response = client.post("/auth/login", json={
        "username": test_user_data["username"],
        "password": "WrongPassword123!"
    })
    
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with non-existent user fails"""
    response = client.post("/auth/login", json={
        "username": "nonexistent",
        "password": "password123"
    })
    
    assert response.status_code == 401


def test_get_current_user(client, test_user_token, test_user_data):
    """Test getting current user info with valid token"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user_data["username"]
    assert data["email"] == test_user_data["email"]


def test_get_current_user_no_token(client):
    """Test getting current user without token fails"""
    response = client.get("/auth/me")
    
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token fails"""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    assert response.status_code == 401
