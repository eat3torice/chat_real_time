#!/usr/bin/env python3
"""
Debug script to check online status
"""
import requests

def check_online_status():
    """Check friends online status for both users"""
    
    # Tokens (you may need to update these)
    user1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhYmMiLCJpYXQiOjE3NjIxNTU2ODMsImV4cCI6MTc2MjE1OTI4M30.cFi5tm84PVF65HW7HWLfwe7c5NpRlApSetYmn8y-Nhs"
    user2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MiwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImlhdCI6MTc2MjE1MTI1MCwiZXhwIjoxNzYyMTU0ODUwfQ.Mjz8wn9UakHzvTRlyCGtWEAEYXcUDP5SgAFTdoCM_zo"
    
    base_url = "http://127.0.0.1:8000"
    
    print("=== User 1 (abc) Friends ===")
    try:
        response = requests.get(f"{base_url}/friends", headers={"Authorization": f"Bearer {user1_token}"})
        if response.status_code == 200:
            friends = response.json()
            for friend in friends:
                status = "🟢 Online" if friend['is_online'] else "⚫ Offline"
                print(f"{friend['username']}: {status}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error checking user 1 friends: {e}")
    
    print("\n=== User 2 (testuser) Friends ===")
    try:
        response = requests.get(f"{base_url}/friends", headers={"Authorization": f"Bearer {user2_token}"})
        if response.status_code == 200:
            friends = response.json()
            for friend in friends:
                status = "🟢 Online" if friend['is_online'] else "⚫ Offline"
                print(f"{friend['username']}: {status}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error checking user 2 friends: {e}")

if __name__ == "__main__":
    check_online_status()