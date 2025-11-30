#!/usr/bin/env python3
"""
Script to update Render service configuration
Fixes the Gunicorn worker class issue
"""
import requests
import json

SERVICE_ID = "srv-d49p4um3jp1c73e6bsqg"
TOKEN = "rnd_n949YjSfZvb3xAJVddMz7Ln1sXSQ"

# New start command using sync worker instead of eventlet
NEW_START_COMMAND = "gunicorn -c gunicorn_config.py wsgi:app"

# Prepare the request
url = f"https://api.render.com/v1/services/{SERVICE_ID}"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "serviceDetails": {
        "envSpecificDetails": {
            "startCommand": NEW_START_COMMAND
        }
    }
}

print(f"Updating Render service {SERVICE_ID}...")
print(f"New start command: {NEW_START_COMMAND}")

try:
    response = requests.patch(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✅ Service updated successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ Exception: {e}")

