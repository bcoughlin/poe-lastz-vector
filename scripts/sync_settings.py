#!/usr/bin/env python3
"""
Manual bot settings sync script for LastZBetaV7_1
"""

import requests

import fastapi_poe as fp

bot_name = "LastZBetaV7_1"
access_key = "fz6Uq6jWbkB9DCq3RVnSxsMiyGlwmmR7"
endpoint_url = "https://bcoughlin--poe-lastz-v7-4b321d-fastapi-app.modal.run"

print(f"Syncing settings for bot: {bot_name}")
print(f"Using endpoint: {endpoint_url}")

try:
    # Use the correct fp.sync_bot_settings signature (bot_name, access_key)
    result = fp.sync_bot_settings(bot_name, access_key)
    print(f"Sync result: {result}")
except Exception as e:
    print(f"Sync failed: {e}")

    # Try direct test of settings endpoint
    print("\nTesting settings endpoint directly...")
    try:
        response = requests.post(
            endpoint_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_key}",
            },
            json={"version": "1.0", "type": "settings"},
        )
        print(f"Direct test status: {response.status_code}")
        print(f"Direct test response: {response.text}")
    except Exception as direct_e:
        print(f"Direct test failed: {direct_e}")
