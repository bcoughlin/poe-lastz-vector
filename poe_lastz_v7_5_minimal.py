"""
Last Z: Minimal Assistant V7.5 - Tool Calling with Local Data
Uses Poe function calling to let GPT decide when to access game data.
"""

import hashlib
import json
import os
from collections.abc import AsyncIterable
from datetime import datetime

import fastapi_poe as fp
from modal import App, Image, asgi_app

# Generate hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%H:%M")

# Bot credentials
bot_access_key = "DjeSMuL0QwiwBSLa33Pa6t97kxhEmmXb"
bot_name = "LastZBetaV7"

# Tool function that GPT can call
def get_lastz_data(query_type: str = "heroes") -> str:
    """
    Get Last Z game data from local mounted files.
    
    Args:
        query_type: Type of data to retrieve - "heroes", "buildings", "equipment", etc.
    
    Returns:
        JSON string with relevant game data
    """
    try:
        print(f"🔧 Tool called: get_lastz_data('{query_type}')")
        
        # Check what data is available
        data_path = "/app/data"
        if not os.path.exists(data_path):
            return json.dumps({"error": "Data mount not found"})
        
        result = {"query_type": query_type, "data": []}
        
        # Handle different query types
        if "hero" in query_type.lower():
            heroes_path = f"{data_path}/heroes"
            if os.path.exists(heroes_path):
                hero_files = [f for f in os.listdir(heroes_path) if f.endswith('.json')][:5]
                for hero_file in hero_files:
                    try:
                        with open(f"{heroes_path}/{hero_file}", 'r') as f:
                            hero_data = json.load(f)
                            result["data"].append({
                                "name": hero_data.get("name", hero_file),
                                "role": hero_data.get("role", "Unknown"),
                                "rarity": hero_data.get("rarity", "Unknown")
                            })
                    except Exception as e:
                        print(f"Error reading {hero_file}: {e}")
        
        elif "building" in query_type.lower() or "hq" in query_type.lower():
            buildings_file = f"{data_path}/buildings.json"
            if os.path.exists(buildings_file):
                try:
                    with open(buildings_file, 'r') as f:
                        buildings = json.load(f)
                    result["data"] = buildings[:3]  # First 3 buildings
                except Exception as e:
                    result["error"] = f"Error reading buildings: {e}"
        
        else:
            # General data listing
            files = [f for f in os.listdir(data_path) if f.endswith('.json')][:5]
            result["available_files"] = files
            result["data"] = f"Available data types: {', '.join(files)}"
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        print(f"❌ Tool error: {e}")
        return json.dumps({"error": str(e)})

# Tool definitions for GPT
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "get_lastz_data",
            "description": "Get Last Z game data including heroes, buildings, equipment, and strategy information. Call this when users ask about game content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "Type of data to retrieve: 'heroes', 'buildings', 'equipment', 'strategy', or 'general'",
                        "enum": ["heroes", "buildings", "equipment", "strategy", "general"]
                    }
                },
                "required": ["query_type"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

tool_definitions_fp = [fp.ToolDefinition(**tool_dict) for tool_dict in tool_definitions]
tool_executables = [get_lastz_data]

class LastZMinimalBot(fp.PoeBot):
    def sanitize_text(self, text):
        """Basic text sanitization for GPT compatibility"""
        if not text:
            return text
        # Replace most common problematic characters
        replacements = {
            "'": "'", "'": "'", """: '"', """: '"',
            "—": "--", "–": "--", "…": "..."
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Convert to ASCII
        try:
            return text.encode('ascii', 'replace').decode('ascii')
        except Exception:
            return ''.join(char for char in text if ord(char) < 128)

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """Use function calling to let GPT access game data when needed"""
        # Sanitize the user message
        if request.query:
            sanitized_query = []
            for msg in request.query:
                sanitized_content = self.sanitize_text(msg.content)
                sanitized_query.append(fp.ProtocolMessage(
                    role=msg.role,
                    content=sanitized_content,
                    message_type=getattr(msg, 'message_type', None)
                ))
            
            sanitized_request = fp.QueryRequest(
                version=request.version,
                type=request.type,
                query=sanitized_query,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                message_id=request.message_id,
                access_key=request.access_key
            )
        else:
            sanitized_request = request
        
        # Stream with tool calling enabled
        async for msg in fp.stream_request(
            sanitized_request,
            "GPT-5",
            request.access_key,
            tools=tool_definitions_fp,
            tool_executables=tool_executables,
        ):
            yield msg

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            allow_attachments=False,
            introduction_message=f"Last Z Assistant V7.5 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🎯 Last Z strategy helper with tool calling\n\nI can access live game data about heroes, buildings, and equipment. Just ask naturally about any Last Z topic!\n\n💡 Try: 'What heroes are available?' or 'Tell me about headquarters upgrades'"
        )

# Modal setup with local data mounting
REQUIREMENTS = ["fastapi-poe"]
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env({"POE_ACCESS_KEY": bot_access_key, "POE_BOT_NAME": bot_name})
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
)
app = App(f"poe-lastz-v7-5-minimal-{deploy_hash}")

@app.function(image=image)
@asgi_app()
def fastapi_app():
    bot = LastZMinimalBot()
    return fp.make_app(
        bot,
        access_key=bot_access_key,
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name),
    )

if __name__ == "__main__":
    print("🧪 Testing minimal local data access...")
    try:
        bot = LastZMinimalBot()
        test_result = bot.get_basic_knowledge("natalie hero")
        print(f"✅ Test result: {test_result[:100]}...")
    except Exception as e:
        print(f"❌ Test failed: {e}")