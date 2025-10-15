"""
Last Z: Survival Shooter Assistant V5.9 - Proper Tool Calling with MCP 3.1
A Poe bot for strategic advice in Last Z: Survival Shooter game.
Uses GPT-5 with ToolDefinition and tool_executables for working tool integration.
"""

import asyncio
import os
import json
import requests
from datetime import datetime
from typing import Any, AsyncIterable
import hashlib

import fastapi_poe as fp
import modal

# Generate short hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]

# Create new Modal app instance for V5.9 with MCP 3.1
app = modal.App("poe-lastz-v5_9-mcp-3_1-41852f")

# Configure Modal image with dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi-poe==0.0.48",
    "requests",
)

# Mount data volume for Last Z game data
volume = modal.Volume.from_name("lastz-data", create_if_missing=False)

class LastZAssistant(fp.PoeBot):
    """Last Z game strategy assistant powered by GPT-5 with working tool integration."""
    
    def __init__(self, access_key: str):
        super().__init__()
        self.access_key = access_key
        # Note: Using proper ToolDefinition and tool_executables with fp.stream_request()
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text to prevent Unicode encoding errors."""
        if not text:
            return text
            
        # Replace problematic Unicode characters with ASCII equivalents
        replacements = {
            '\u2019': "'",  # Right single quotation mark
            '\u2018': "'",  # Left single quotation mark  
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Horizontal ellipsis
        }
        
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
            
        # Ensure only ASCII characters remain
        try:
            text.encode('ascii')
            return text
        except UnicodeEncodeError:
            # If there are still non-ASCII chars, encode/decode to remove them
            return text.encode('ascii', errors='ignore').decode('ascii')
    
    def get_lastz_knowledge(self, topic: str) -> str:
        """
        Get Last Z game knowledge from comprehensive database.
        
        Args:
            topic: The game topic to research (e.g., "headquarters", "heroes", "research")
        """
        print(f"DEBUG: get_lastz_knowledge called with topic: {topic}")
        try:
            # Use the v3.1 MCP service with proper authentication and endpoint
            headers = {"Authorization": "Bearer dev-key-12345"}
            response = requests.get(
                "https://bcoughlin--lastz-mcp-v3-1-serve-modal.modal.run/knowledge",
                params={"topic": topic},
                headers=headers,
                timeout=10
            )
            
            print(f"DEBUG: MCP response status: {response.status_code}")
            print(f"DEBUG: MCP response: {response.text[:200]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Extract the actual knowledge content
                    knowledge = data.get("knowledge", {})
                    if knowledge:
                        import json
                        return json.dumps(knowledge, indent=2)
                    return data.get("content", f"Found information about {topic}")
                except json.JSONDecodeError:
                    return f"Retrieved data for {topic}: {response.text[:500]}"
            else:
                return f"Could not retrieve {topic} information (status: {response.status_code})"
                
        except Exception as e:
            print(f"DEBUG: MCP error: {str(e)}")
            return f"Error accessing Last Z database for {topic}: {str(e)}"
    
    def analyze_lastz_screenshot(self, description: str) -> str:
        """
        Analyze a Last Z game screenshot for strategic advice.
        
        Args:
            description: Description of what the user sees in their screenshot
        """
        return f"Screenshot analysis for: {description}. Based on what you've described, I can provide strategic recommendations. Please share more details about your current game state, level, and what specific guidance you need."

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        """Return bot settings."""
        # Generate fresh deployment timestamp
        deploy_time = datetime.now().strftime("%Y%m%d_%H%M")
        
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            allow_attachments=True,
            introduction_message=(
                f"Last Z: Survival Shooter Assistant V5.9 MCP 3.1 ({deploy_time})\n\n"
                "I'm your strategic advisor for Last Z: Survival Shooter powered by GPT-5!\n\n"
                "I can help you with:\n"
                "- Hero Analysis - Stats, abilities, and optimization strategies\n"
                "- Building Guide - Headquarters and facility progression\n"
                "- Strategic Advice - Leveling, resource management, and gameplay tips\n"
                "- Screenshot Analysis - Describe what you see for strategic advice\n\n"
                "Data Source: MCP v3.1 service with latest Last Z game data\n\n"
                "Ask me anything about Last Z strategy and I'll provide intelligent, data-driven advice!"
            ),
        )

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """Generate intelligent responses using GPT-5 with proper tool calling."""
        
        # Get the latest user message
        last_message = request.query[-1] if request.query else None
        user_message = last_message.content if last_message else ""
        
        # Sanitize the user message
        sanitized_message = self.sanitize_text(user_message)
        
        # Define tool definitions for GPT-5
        tool_definitions = [
            fp.ToolDefinition(
                type="function",
                function=fp.ToolDefinition.FunctionDefinition(
                    name="get_lastz_knowledge",
                    description="Get Last Z game knowledge from comprehensive database. Use for hero stats, building requirements, upgrade paths, and other specific game data.",
                    parameters=fp.ToolDefinition.FunctionDefinition.ParametersDefinition(
                        type="object",
                        properties={
                            "topic": {
                                "type": "string", 
                                "description": "The game topic to research (e.g., 'headquarters', 'heroes', 'research')"
                            }
                        },
                        required=["topic"]
                    )
                )
            ),
            fp.ToolDefinition(
                type="function", 
                function=fp.ToolDefinition.FunctionDefinition(
                    name="analyze_lastz_screenshot",
                    description="Analyze a Last Z game screenshot for strategic advice based on what the user describes seeing.",
                    parameters=fp.ToolDefinition.FunctionDefinition.ParametersDefinition(
                        type="object",
                        properties={
                            "description": {
                                "type": "string",
                                "description": "Description of what the user sees in their screenshot" 
                            }
                        },
                        required=["description"]
                    )
                )
            )
        ]
        
        # Tool executables that correspond to the definitions
        tool_executables = [self.get_lastz_knowledge, self.analyze_lastz_screenshot]
        
        # Enhanced system prompt
        system_prompt = (
            "You are a Last Z: Survival Shooter strategy expert with access to a comprehensive game database. "
            "When users ask for specific game details (hero stats, building requirements, upgrade paths), use the get_lastz_knowledge tool to fetch accurate data. "
            "For screenshot analysis, use the analyze_lastz_screenshot tool. "
            "Always prioritize tool-provided data over general knowledge for specific game mechanics."
        )
        
        # Build query with system prompt
        enhanced_query = [
            fp.ProtocolMessage(role="system", content=system_prompt),
            fp.ProtocolMessage(role="user", content=sanitized_message)
        ]
        
        # Create sanitized request for GPT-5 with tools
        sanitized_request = fp.QueryRequest(
            query=enhanced_query,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            version=request.version,
            type=request.type,
        )
        
        # Get access key from environment (injected by Modal secrets)
        access_key = self.access_key
        print(f"DEBUG: Access key length: {len(access_key) if access_key else 0}")
        
        # Stream response from GPT-5 with tool calling capabilities
        async for msg in fp.stream_request(
            sanitized_request,
            "GPT-5",
            api_key=access_key,
            tools=tool_definitions,
            tool_executables=tool_executables
        ):
            yield msg

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("poe-secrets")
    ],
    volumes={"/data": volume},
)
@modal.asgi_app()
def serve():
    """Serve the LastZ Assistant bot."""
    # Get configuration from environment
    access_key = os.getenv("POE_ACCESS_KEY")
    print(f"DEBUG: serve() access_key length: {len(access_key) if access_key else 0}")
    if not access_key:
        raise ValueError("POE_ACCESS_KEY not found in environment")
    
    bot_name = os.getenv("POE_BOT_NAME", "LastZv5.9")
    
    # Create bot instance with access key
    bot = LastZAssistant(access_key)
    
    # Create FastAPI app with ASGI (bot already has access key)
    fastapi_app = fp.make_app(bot, bot_name=bot_name)
    return fastapi_app

if __name__ == "__main__":
    # For local testing
    from fastapi_poe import run
    bot = LastZAssistant("your-local-access-key")
    run(bot, access_key="your-local-access-key")