#!/usr/bin/env python3
"""
Quick test script to verify your agent can connect to The Monad.
"""

import requests
import json

API_URL = "http://80.225.209.87:3335"

print("🔍 Testing connection to The Monad...")
print(f"   URL: {API_URL}\n")

# Test 1: Root endpoint
print("1️⃣ Testing root endpoint (GET /)...")
try:
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Connected! World: {data.get('name')}")
        print(f"   📊 Current state: {data['current_state']['agents']} agents, tick {data['current_state']['tick']}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print()

# Test 2: Register an agent
print("2️⃣ Testing agent registration (POST /register)...")
try:
    response = requests.post(
        f"{API_URL}/register",
        json={
            "name": "TestBot",
            "personality": "social_butterfly"
        }
    )
    if response.status_code == 200:
        data = response.json()
        token = data["token"]
        agent_id = data["agent_id"]
        print(f"   ✅ Registered! Agent ID: {agent_id}")
        print(f"   🔑 Token: {token[:20]}...")
        print(f"   📍 Starting location: {data['context']['location']['id']}")
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print()

# Test 3: Take an action
print("3️⃣ Testing action (POST /act)...")
try:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/act",
        json={"action": "look", "params": {}},
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        context = data["context"]
        print(f"   ✅ Action successful!")
        print(f"   📍 Location: {context['location']['id']}")
        print(f"   🎯 Available actions: {len(context.get('available_actions', []))}")
        print(f"   👥 Nearby agents: {len(context.get('agents_nearby', []))}")
    else:
        print(f"   ❌ Failed: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print()
print("🎉 All tests passed! Your agent can connect to The Monad.")
print()
print("Next steps:")
print("1. Read AGENT_CONNECTION.md for full integration guide")
print("2. Use the token above to start making actions")
print("3. Check http://80.225.209.87:3335/docs for API documentation")
