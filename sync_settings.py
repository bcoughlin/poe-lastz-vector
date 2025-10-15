#!/usr/bin/env python3
"""
Manual bot settings sync script for LastZTestV3
"""
import fastapi_poe as fp

# Replace with your bot information
bot_name = "LastZTestV3"
access_key = "HjospevIfYHwgw2emgwW3GzObV3xv7Xq"

print(f"Syncing settings for bot: {bot_name}")
result = fp.sync_bot_settings(bot_name, access_key)
print(f"Sync result: {result}")