"""
Data collection utilities for Last Z Bot
Handles interaction logging and image storage
"""

import json
import os
from datetime import datetime
from typing import Any

import requests

# Data storage configuration
DATA_STORAGE_PATH = os.environ.get("DATA_STORAGE_PATH", "/tmp/lastz_data")
INTERACTIONS_PATH = os.path.join(DATA_STORAGE_PATH, "interactions")
IMAGES_PATH = os.path.join(DATA_STORAGE_PATH, "images")

# Ensure storage directories exist
os.makedirs(INTERACTIONS_PATH, exist_ok=True)
os.makedirs(IMAGES_PATH, exist_ok=True)


def create_interaction_log(
    user_id: str,
    conversation_id: str,
    message_id: str,
    user_message: str,
    bot_response: str,
    has_images: bool = False,
    image_count: int = 0,
    image_data: list[dict[str, Any]] = None,
    tool_calls: list[str] = None,
    response_time: float = 0.0,
    deploy_hash: str = "",
) -> dict[str, Any]:
    """Create a structured log entry for user interactions"""
    return {
        "timestamp": datetime.now().isoformat(),
        "session_info": {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
        },
        "interaction": {
            "user_message": user_message,
            "user_message_length": len(user_message),
            "has_images": has_images,
            "image_count": image_count,
            "image_data": image_data or [],
            "bot_response": bot_response,
            "bot_response_length": len(bot_response),
            "response_time_ms": round(response_time * 1000, 2),
        },
        "metadata": {
            "tool_calls": tool_calls or [],
            "bot_version": "0.8.2-modular",
            "deploy_hash": deploy_hash,
            "hosting": "render",
        },
    }


def log_interaction_to_console(interaction_data: dict[str, Any]):
    """Log interaction data to console"""
    print("\n" + "=" * 80)
    print("📊 INTERACTION LOGGED")
    print("=" * 80)
    print(f"🕐 Timestamp: {interaction_data['timestamp']}")
    print(f"👤 User ID: {interaction_data['session_info']['user_id']}")
    print(f"💬 Message: {interaction_data['interaction']['user_message'][:100]}...")
    print(f"🖼️  Images: {interaction_data['interaction']['image_count']}")
    print(f"🔧 Tools: {', '.join(interaction_data['metadata']['tool_calls'])}")
    print(f"⏱️  Response Time: {interaction_data['interaction']['response_time_ms']}ms")
    print("=" * 80)


def store_interaction_data(interaction_data: dict[str, Any]) -> bool:
    """Store interaction data to filesystem"""
    try:
        timestamp = interaction_data["timestamp"].replace(":", "-").replace(".", "-")
        message_id = interaction_data["session_info"]["message_id"]
        filename = f"interaction_{timestamp}_{message_id}.json"

        filepath = os.path.join(INTERACTIONS_PATH, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(interaction_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Stored interaction: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Failed to store interaction: {e}")
        return False


def download_and_store_image(
    image_url: str, image_name: str, user_id: str, message_id: str
) -> str | None:
    """Download and store image from URL"""
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        safe_name = "".join(
            c for c in image_name if c.isalnum() or c in ("_", "-", ".")
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{message_id}_{timestamp}_{safe_name}"

        filepath = os.path.join(IMAGES_PATH, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded image: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return None
