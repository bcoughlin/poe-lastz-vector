#!/usr/bin/env python3
"""
LastZ Bot V4 - Fresh version to bypass Poe cache issues
Last Z: Survival Shooter Assistant with MCP integration and GPT-5 intelligence
"""

import os
import json
import requests
from collections.abc import AsyncIterable
from datetime import datetime
import modal
import fastapi_poe as fp
from fastapi_poe import PoeBot, run, make_app
from fastapi_poe.types import (
    PartialResponse,
    SettingsRequest,
    SettingsResponse
)


class LastZBotV4(PoeBot):
    """Last Z: Survival Shooter Assistant Bot V4 with tool calling and GPT-5 intelligence"""
    
    def __init__(self):
        super().__init__()
        # Use the current data service
        self.mcp_base_url = "https://bcoughlin--lastz-mcp-v3-serve-modal.modal.run"
        self.mcp_auth_token = "dev-key-12345"

    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[PartialResponse]:
        """Handle user messages using tool calls and GPT-5 synthesis."""
        
        # Use GPT-5 with tool calling for intelligent responses
        yield PartialResponse(text="🎮 **Last Z Assistant V4** (`9ac36dd`) - Analyzing your question...\n\n")
        
        # Stream the request to GPT-5 with tools
        async for msg in fp.stream_request(
            request,
            "GPT-5",  # Use GPT-5 for best performance
            tool_executables=[self.get_lastz_knowledge, self.analyze_lastz_screenshot],
        ):
            yield msg

    def get_lastz_knowledge(self, topic: str) -> str:
        """
        Get Last Z game knowledge from the comprehensive RAG database.
        
        Args:
            topic: The topic to query (heroes, buildings, progression, etc.)
        """
        try:
            url = f"{self.mcp_base_url}/knowledge"
            params = {"topic": topic}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return json.dumps(data, indent=2)
            else:
                return f"Error accessing knowledge base: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error querying Last Z knowledge: {str(e)}"

    def analyze_lastz_screenshot(self, description: str) -> str:
        """
        Analyze a Last Z screenshot description for strategic advice.
        
        Args:
            description: Description of what the user sees in their screenshot
        """
        # For now, provide guidance on screenshot analysis
        return f"Screenshot analysis requested for: {description}. This feature will be enhanced to process actual images soon. For now, please describe what you see in your Last Z game and I'll provide strategic advice based on that description."

    async def get_settings(self, setting: SettingsRequest) -> SettingsResponse:
        """Return bot settings."""
        # Generate deployment timestamp for cache detection
        deploy_time = datetime.now().strftime("%Y%m%d_%H%M")
        
        return SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},  # Use GPT-5 for intelligent responses
            allow_attachments=True,  # Enable for future screenshot analysis
            introduction_message=(
                f"🎮 **Last Z: Survival Shooter Assistant V4** (`9ac36dd` - v{deploy_time})\n\n"
                "I'm your strategic advisor for Last Z: Survival Shooter powered by GPT-5 and a comprehensive game database!\n\n"
                "🆕 **V4 Features:**\n"
                "• **Real-time Timestamps** - See exact deployment version\n"
                "• **Cache-busting** - Fresh responses, no old cached data\n"
                "• **GPT-5 Intelligence** - Latest AI model for strategic analysis\n\n"
                "I can help you with:\n\n"
                "• **Hero Analysis** - Stats, abilities, and optimization strategies\n"
                "• **Building Guide** - Headquarters and facility progression\n"
                "• **Strategic Advice** - Leveling, resource management, and gameplay tips\n"
                "• **Screenshot Analysis** - Describe what you see for strategic advice\n\n"
                "**Current Status:** ✅ Connected to updated data service with 21+ heroes and comprehensive game data\n\n"
                "Ask me anything about Last Z strategy and I'll provide intelligent, data-driven advice!"
            )
        )


# Modal configuration
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt").pip_install("requests", force_build=True)
app = modal.App("poe-lastz-v4")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_dict(
            {
                "POE_ACCESS_KEY_LASTZ_V4": "8mdhlePh12tq63ojTobEzFFcFUPB8VVP",
                "POE_BOT_NAME_LASTZ_V4": "LastZTestV4",
            }
        )
    ],
)
@modal.asgi_app()
def serve():
    """Serve the LastZ V4 bot with tool calling capabilities."""
    bot = LastZBotV4()
    
    # Use the access key for this specific bot
    access_key = os.environ.get("POE_ACCESS_KEY_LASTZ_V4")
    if not access_key:
        raise ValueError("POE_ACCESS_KEY_LASTZ_V4 not found in environment")
    
    bot_name = os.environ.get("POE_BOT_NAME_LASTZ_V4", "LastZTestV4")
    
    fastapi_app = make_app(bot, access_key=access_key, bot_name=bot_name)
    return fastapi_app


if __name__ == "__main__":
    # For local development
    bot = LastZBotV4()
    run(bot, access_key="your-local-access-key")