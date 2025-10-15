"""
Last Z: Survival Shooter Assistant V7.4 Simple - Working v7.3 + Local Mount
Exactly copying the working v7.3 pattern but with local data mount
"""

import hashlib
import os
import json
import re
from collections.abc import AsyncIterable
from datetime import datetime

import modal
import numpy as np

import fastapi_poe as fp

# Generate hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%H:%M")

# Modal app
app = modal.App(f"poe-lastz-v7-4-simple-{deploy_hash}")

# Create image with dependencies and local data mount
image = (
    modal.Image.debian_slim()
    .pip_install([
        "fastapi-poe==0.0.48",
        "sentence-transformers",
        "scikit-learn", 
        "numpy",
        "pyyaml"
    ])
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
)

class LastZSimpleBot:
    def __init__(self):
        self._knowledge_items = []
        self._embeddings = None
        self._encoder = None

    async def get_response_content(self, query):
        """Basic response - focus on testing local mount"""
        user_message = query.query[-1].content if query.query else ""
        
        # Try to access local mounted data
        try:
            data_index_path = "/app/data/core/data_index.md"
            if os.path.exists(data_index_path):
                with open(data_index_path, 'r') as f:
                    content = f.read()
                response_msg = f"✅ Local mount working! Found data_index.md with {len(content)} characters. Your question: {user_message}"
            else:
                response_msg = f"❌ Local mount failed - data_index.md not found. Your question: {user_message}"
        except Exception as e:
            response_msg = f"❌ Error accessing local mount: {e}. Your question: {user_message}"
        
        # Simple text response
        yield fp.PartialResponse(text=response_msg)

@app.function(
    image=image,
    secrets=[modal.Secret.from_dict({
        "POE_ACCESS_KEY": "DjeSMuL0QwiwBSLa33Pa6t97kxhEmmXb", 
        "POE_BOT_NAME": "LastZBetaV7",
    })]
)
@modal.asgi_app()
def fastapi_app():
    bot = LastZSimpleBot()
    return fp.make_app([bot])  # API expects list of bots

@app.function(image=image)
def get_settings():
    return fp.SettingsResponse(
        server_bot_dependencies={"GPT-5": 1},
        allow_attachments=True,
        introduction_message=f"Last Z Simple Test V7.4 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🧪 **Testing local data mount**\n\nAsk any question to test if local data is accessible!"
    )

if __name__ == "__main__":
    bot = LastZSimpleBot()
    print("Local test - checking data access...")
    try:
        if os.path.exists("/Users/bradleycoughlin/local_code/lastz-rag/data/core/data_index.md"):
            print("✅ Local data file exists")
        else:
            print("❌ Local data file not found")
    except Exception as e:
        print(f"❌ Error: {e}")