"""
Last Z: Survival Shooter Game Analysis Bot for Poe Platform - Version 2

A sophisticated bot that analyzes Last Z screenshots and provides strategic advice
using the lastz-rag MCP service for dynamic knowledge retrieval.

Built with lessons learned from test bot for reliable multi-message handling.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterable

import modal

from fastapi_poe import PoeBot, make_app
from fastapi_poe.types import (
    PartialResponse,
    QueryRequest,
    SettingsRequest,
    SettingsResponse,
)


class LastZBotV2(PoeBot):
    """A bot that analyzes Last Z screenshots and provides strategic game advice using lastz-rag MCP service."""

    def __init__(self) -> None:
        super().__init__()
        # LastZ MCP service endpoint
        self.mcp_base_url = "https://bcoughlin--lastz-mcp-service-v2-serve.modal.run"

    async def get_response(
        self, request: QueryRequest
    ) -> AsyncIterable[PartialResponse]:
        """Generate strategic Last Z advice and screenshot analysis."""

        # Get the user's message safely
        last_message = request.query[-1] if request.query else None
        message_content = last_message.content if last_message else "No message"
        
        yield PartialResponse(text="🎮 **Last Z: Survival Shooter Assistant**\n\n")
        
                # Check if user is asking about heroes
        if any(keyword in message_content.lower() for keyword in ["hero", "heroes", "sophia", "zeta", "combat"]):
            yield PartialResponse(text="🦸 Retrieving hero knowledge from Last Z database...\n\n")
            heroes_info = self.get_heroes_knowledge()
            yield PartialResponse(text=f"{heroes_info}\n\n")
            
        # Check if user is asking about buildings/HQ
        elif any(keyword in message_content.lower() for keyword in ["building", "hq", "headquarters"]):
            yield PartialResponse(text="🏗️ Retrieving building knowledge from Last Z database...\n\n")
            buildings_info = self.get_buildings_knowledge()
            yield PartialResponse(text=f"{buildings_info}\n\n")
            
        # Check if user is asking about progression
        elif "progress" in message_content.lower() or "level" in message_content.lower():
            yield PartialResponse(text="📈 Retrieving progression strategies from Last Z database...\n\n")
            progression_info = self.get_progression_knowledge()
            yield PartialResponse(text=f"{progression_info}\n\n")
            
        # BULK DATA TEST - for accuracy verification
        elif "bulk" in message_content.lower() or "all data" in message_content.lower() or "complete" in message_content.lower():
            yield PartialResponse(text="📊 Retrieving COMPLETE Last Z dataset for accuracy testing...\n\n")
            bulk_data = self.get_bulk_data()
            yield PartialResponse(text=f"{bulk_data}\n\n")
            
        # General Last Z help
        else:
            yield PartialResponse(text=f"I received your message: '{message_content}'\n\n")
            yield PartialResponse(text="I can help you with:\n")
            yield PartialResponse(text="• **Heroes** - Ask about hero stats, abilities, and optimization\n")
            yield PartialResponse(text="• **Buildings** - Ask about headquarters and building progression\n")
            yield PartialResponse(text="• **Progression** - Ask about leveling strategies and game progression\n")
            yield PartialResponse(text="• **Bulk Data** - Say 'bulk data' to get complete dataset for accuracy testing\n")
            yield PartialResponse(text="• **Screenshots** - Upload Last Z screenshots for analysis (coming soon)\n\n")
            
            # Test MCP connectivity
            yield PartialResponse(text="🔍 Testing Last Z knowledge base connectivity...\n")
            connectivity_test = self.test_mcp_connectivity()
            yield PartialResponse(text=f"{connectivity_test}\n\n")
        
        yield PartialResponse(text="💡 **Tip**: Try asking about heroes, buildings, or progression strategies!")

    def get_heroes_knowledge(self) -> str:
        """Get hero-related knowledge from LastZ MCP service."""
        try:
            import requests
            response = requests.get(
                f"{self.mcp_base_url}/knowledge",
                params={"topic": "heroes"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                knowledge = data.get('knowledge', {})
                
                # Extract hero information
                heroes_data = knowledge.get('heroes', {})
                if 'heroes' in heroes_data:
                    hero_list = heroes_data['heroes']
                    if hero_list:
                        result = "🦸 **Hero Information:**\n\n"
                        for hero in hero_list[:3]:  # Show first 3 heroes
                            name = hero.get('name', 'Unknown')
                            hero_type = hero.get('type', 'Unknown')
                            function = hero.get('function', 'No description')
                            result += f"• **{name}** ({hero_type}): {function}\n"
                        return result
                
                # Fallback to guide if available
                heroes_guide = knowledge.get('heroes_guide', '')
                if heroes_guide:
                    return f"📖 **Hero Strategy Guide:**\n\n{heroes_guide[:500]}..."
                
                return "✅ Connected to Last Z knowledge base, but no hero data found."
            else:
                return f"❌ Failed to retrieve hero knowledge (status: {response.status_code})"
                
        except Exception as e:
            return f"❌ Error retrieving hero knowledge: {str(e)}"

    def get_buildings_knowledge(self) -> str:
        """Get building-related knowledge from LastZ MCP service."""
        try:
            import requests
            response = requests.get(
                f"{self.mcp_base_url}/knowledge",
                params={"topic": "buildings"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                knowledge = data.get('knowledge', {})
                
                # Look for building information
                if knowledge:
                    return f"🏗️ **Building Knowledge Retrieved:**\n\nFound {len(knowledge)} knowledge sections about buildings and progression."
                else:
                    return "✅ Connected to Last Z knowledge base, but no building data found."
            else:
                return f"❌ Failed to retrieve building knowledge (status: {response.status_code})"
                
        except Exception as e:
            return f"❌ Error retrieving building knowledge: {str(e)}"

    def get_progression_knowledge(self) -> str:
        """Get progression-related knowledge from LastZ MCP service."""
        try:
            import requests
            response = requests.get(
                f"{self.mcp_base_url}/knowledge",
                params={"topic": "progression"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                knowledge = data.get('knowledge', {})
                
                if knowledge:
                    return f"📈 **Progression Knowledge Retrieved:**\n\nFound strategic information about game progression and leveling."
                else:
                    return "✅ Connected to Last Z knowledge base, but no progression data found."
            else:
                return f"❌ Failed to retrieve progression knowledge (status: {response.status_code})"
                
        except Exception as e:
            return f"❌ Error retrieving progression knowledge: {str(e)}"

    def test_mcp_connectivity(self) -> str:
        """Test basic connectivity to LastZ MCP service."""
        try:
            import requests
            response = requests.get(f"{self.mcp_base_url}/health", timeout=10.0)
            
            if response.status_code == 200:
                return "✅ Last Z knowledge base is online and ready!"
            else:
                return f"⚠️ Last Z knowledge base responded with status {response.status_code}"
                
        except Exception as e:
            return f"❌ Cannot connect to Last Z knowledge base: {str(e)}"

    def get_bulk_data(self) -> str:
        """Get complete LastZ dataset for accuracy testing."""
        try:
            import requests
            response = requests.get(
                f"{self.mcp_base_url}/bulk-data",
                timeout=60.0  # Longer timeout for bulk data
            )
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('dataset_summary', {})
                
                result = "📊 **COMPLETE LASTZ DATASET** (for accuracy verification)\n\n"
                result += f"**Dataset Summary:**\n"
                result += f"• Heroes: {summary.get('heroes_count', 0)}\n"
                result += f"• Data Types: {len(summary.get('data_files_included', []))}\n"
                result += f"• Total Data Points: {summary.get('total_data_points', 0)}\n\n"
                
                # List available data types
                data_types = summary.get('data_files_included', [])
                if data_types:
                    result += f"**Available Data Types:**\n"
                    for data_type in data_types:
                        result += f"• {data_type.replace('_', ' ').title()}\n"
                
                # Show sample data for verification
                if 'heroes_index' in data:
                    heroes_index = data['heroes_index']
                    heroes = heroes_index.get('heroes', [])
                    if heroes:
                        result += f"\n**Sample Heroes Data (first 5):**\n"
                        for hero in heroes[:5]:
                            result += f"• {hero.get('name', 'Unknown')} ({hero.get('rarity', 'Unknown')}, {hero.get('faction', 'Unknown')})\n"
                
                if 'buildings' in data:
                    buildings = data['buildings'].get('buildings', [])
                    if buildings:
                        result += f"\n**Sample Buildings Data (first 3):**\n"
                        for building in buildings[:3]:
                            result += f"• {building.get('name', 'Unknown')} - {building.get('type', 'Unknown')}\n"
                
                result += f"\n**Note:** This is the complete dataset I use to answer your questions. You can verify my responses against this data to check for accuracy vs hallucinations."
                return result
                
            else:
                return f"❌ Failed to retrieve bulk data (status {response.status_code})"
                
        except Exception as e:
            return f"❌ Cannot retrieve bulk data: {str(e)}"

    async def get_settings(self, setting: SettingsRequest) -> SettingsResponse:
        """Return bot settings."""
        return SettingsResponse(
            server_bot_dependencies={},  # No GPT-4 dependency for direct responses
            allow_attachments=False,  # Will enable for screenshot analysis later
            introduction_message=(
                "🎮 **Last Z: Survival Shooter Assistant**\n\n"
                "I'm your strategic advisor for Last Z: Survival Shooter! I can help you with:\n\n"
                "• **Hero Analysis** - Stats, abilities, and optimization strategies\n"
                "• **Building Guide** - Headquarters and facility progression\n"
                "• **Strategic Advice** - Leveling, resource management, and gameplay tips\n"
                "• **Screenshot Analysis** - Coming soon!\n\n"
                "Ask me about heroes, buildings, progression, or any Last Z strategy questions!"
            ),
        )


# Modal configuration
image = modal.Image.debian_slim().pip_install_from_requirements("requirements.txt").pip_install("requests")
app = modal.App("lastz-bot-v2")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_dict(
            {
                "POE_ACCESS_KEY_LASTZ_V2": "crDpg2IIdq045iluy9lgWABnyAlZyAXT",
                "POE_BOT_NAME_LASTZ_V2": "LastZBotV2",
            }
        )
    ],
)
@modal.asgi_app()
def serve():
    """Serve the LastZ Bot V2 via Modal."""
    bot = LastZBotV2()

    # Get credentials from environment variables
    POE_ACCESS_KEY = os.getenv("POE_ACCESS_KEY_LASTZ_V2") or os.getenv("POE_ACCESS_KEY")
    POE_BOT_NAME = os.getenv("POE_BOT_NAME_LASTZ_V2") or os.getenv("POE_BOT_NAME")

    # Create the FastAPI app with proper credentials
    if POE_ACCESS_KEY and POE_BOT_NAME:
        app = make_app(bot, access_key=POE_ACCESS_KEY, bot_name=POE_BOT_NAME)
        print(f"✅ LastZ Bot V2 configured with credentials for: {POE_BOT_NAME}")
    else:
        app = make_app(bot, allow_without_key=True)
        print("⚠️  Running without credentials - bot settings won't sync automatically")

    return app


# For local development
if __name__ == "__main__":
    import uvicorn

    bot = LastZBotV2()
    app = make_app(bot, allow_without_key=True)
    uvicorn.run(app, host="0.0.0.0", port=8002)