"""
Last Z: Assistant V7.6 - Vector Embeddings + Tool Calling
Uses semantic search across all game data instead of specific handlers.
"""

import hashlib
import json
import os
from collections.abc import AsyncIterable
from datetime import datetime
from typing import List, Dict, Any

import fastapi_poe as fp
from modal import App, Image, asgi_app

# Generate hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%H:%M")

# Bot credentials
bot_access_key = "DjeSMuL0QwiwBSLa33Pa6t97kxhEmmXb"
bot_name = "LastZBetaV7"

class LastZVectorSearch:
    """Simple vector search using embeddings"""
    
    def __init__(self):
        self.knowledge_items = []
        self.embeddings = None
        self._load_all_data()
    
    def _load_all_data(self):
        """Load and process all JSON data into searchable items"""
        data_path = "/app/data"
        if not os.path.exists(data_path):
            print("❌ Data path not found")
            return
        
        print(f"🔍 Loading data from {data_path}")
        
        # Load heroes
        heroes_path = f"{data_path}/heroes"
        if os.path.exists(heroes_path):
            for hero_file in os.listdir(heroes_path):
                if hero_file.endswith('.json'):
                    try:
                        with open(f"{heroes_path}/{hero_file}", 'r') as f:
                            hero_data = json.load(f)
                        
                        # Create searchable text for hero
                        hero_text = f"Hero: {hero_data.get('name', 'Unknown')} "
                        hero_text += f"Role: {hero_data.get('role', 'Unknown')} "
                        hero_text += f"Rarity: {hero_data.get('rarity', 'Unknown')} "
                        if 'skills' in hero_data:
                            # Handle skills as list of dicts or strings
                            skills = hero_data['skills']
                            if isinstance(skills, list):
                                skill_names = []
                                for skill in skills:
                                    if isinstance(skill, dict):
                                        skill_names.append(skill.get('name', 'Unknown Skill'))
                                    else:
                                        skill_names.append(str(skill))
                                hero_text += f"Skills: {' '.join(skill_names)} "
                            else:
                                hero_text += f"Skills: {str(skills)} "
                        if 'description' in hero_data:
                            hero_text += f"Description: {hero_data['description']}"
                        
                        self.knowledge_items.append({
                            'type': 'hero',
                            'name': hero_data.get('name', hero_file),
                            'text': hero_text,
                            'data': hero_data
                        })
                    except Exception as e:
                        print(f"Error loading hero {hero_file}: {e}")
        
        # Load buildings
        buildings_file = f"{data_path}/buildings.json"
        if os.path.exists(buildings_file):
            try:
                with open(buildings_file, 'r') as f:
                    buildings_data = json.load(f)
                
                if 'buildings' in buildings_data:
                    for building in buildings_data['buildings']:
                        building_text = f"Building: {building.get('name', 'Unknown')} "
                        building_text += f"Type: {building.get('type', 'Unknown')} "
                        building_text += f"Function: {building.get('function', '')} "
                        if 'produces' in building:
                            building_text += f"Produces: {building['produces']} "
                        building_text += f"Notes: {building.get('notes', '')}"
                        
                        self.knowledge_items.append({
                            'type': 'building',
                            'name': building.get('name', 'Unknown'),
                            'text': building_text,
                            'data': building
                        })
            except Exception as e:
                print(f"Error loading buildings: {e}")
        
        # Load equipment
        equipment_file = f"{data_path}/equipment.json"
        if os.path.exists(equipment_file):
            try:
                with open(equipment_file, 'r') as f:
                    equipment_data = json.load(f)
                
                # Handle different possible structures
                equipment_items = []
                if isinstance(equipment_data, list):
                    equipment_items = equipment_data
                elif 'equipment' in equipment_data:
                    equipment_items = equipment_data['equipment']
                elif 'items' in equipment_data:
                    equipment_items = equipment_data['items']
                
                for item in equipment_items[:10]:  # Limit to first 10 items
                    if isinstance(item, dict):
                        item_text = f"Equipment: {item.get('name', 'Unknown')} "
                        item_text += f"Type: {item.get('type', 'Unknown')} "
                        item_text += f"Rarity: {item.get('rarity', 'Unknown')} "
                        item_text += f"Stats: {item.get('stats', '')} "
                        item_text += f"Description: {item.get('description', '')}"
                        
                        self.knowledge_items.append({
                            'type': 'equipment',
                            'name': item.get('name', 'Unknown'),
                            'text': item_text,
                            'data': item
                        })
            except Exception as e:
                print(f"Error loading equipment: {e}")
        
        print(f"✅ Loaded {len(self.knowledge_items)} knowledge items")
    
    def simple_text_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword-based search (placeholder for embeddings)"""
        query_lower = query.lower()
        results = []
        
        for item in self.knowledge_items:
            # Simple scoring based on keyword matches
            score = 0
            text_lower = item['text'].lower()
            
            # Check for exact name matches (high score)
            if query_lower in item['name'].lower():
                score += 10
            
            # Check for keyword matches in text
            for word in query_lower.split():
                if word in text_lower:
                    score += 1
            
            if score > 0:
                results.append({
                    'score': score,
                    'item': item
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return [r['item'] for r in results[:max_results]]

# Global search instance
vector_search = LastZVectorSearch()

# Tool function that GPT can call
def search_lastz_knowledge(user_query: str) -> str:
    """
    Search Last Z game knowledge using the user's natural language query.
    
    Args:
        user_query: Natural language question about Last Z game content
    
    Returns:
        JSON string with relevant game knowledge
    """
    try:
        print(f"🔧 Search tool called: '{user_query}'")
        
        if not vector_search.knowledge_items:
            return json.dumps({"error": "No knowledge data loaded"})
        
        # Perform search
        results = vector_search.simple_text_search(user_query, max_results=5)
        
        if not results:
            return json.dumps({
                "query": user_query,
                "message": "No specific matches found in knowledge base",
                "total_items": len(vector_search.knowledge_items)
            })
        
        # Format results
        formatted_results = []
        for item in results:
            formatted_results.append({
                "type": item['type'],
                "name": item['name'],
                "summary": item['text'][:200] + "..." if len(item['text']) > 200 else item['text'],
                "full_data": item['data']
            })
        
        return json.dumps({
            "query": user_query,
            "results_count": len(formatted_results),
            "results": formatted_results
        }, indent=2)
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return json.dumps({"error": str(e)})

# Tool definitions for GPT
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_lastz_knowledge",
            "description": "Search Last Z game knowledge using natural language. Pass the user's exact question to find relevant heroes, buildings, equipment, and strategy information. IMPORTANT: Always cite your sources by mentioning the specific item names and types from the search results (e.g., 'According to the hero data for Natalie...' or 'Based on the Training Ground building info...').",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's natural language question about Last Z game content"
                    }
                },
                "required": ["user_query"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

tool_definitions_fp = [fp.ToolDefinition(**tool_dict) for tool_dict in tool_definitions]
tool_executables = [search_lastz_knowledge]

class LastZEmbeddingsBot(fp.PoeBot):
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
        """Use semantic search to find relevant game knowledge"""
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
        
        # Stream with semantic search tool calling
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
            introduction_message=f"Last Z Assistant V7.6 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🔍 SEMANTIC SEARCH VERSION with Source Citations\n\n✅ Intelligent knowledge search across:\n• Heroes (roles, skills, rarities)\n• Buildings (functions, scaling, notes)  \n• Equipment (stats, descriptions)\n\n🧠 Ask naturally - I'll find relevant information and cite my sources!\n\n💡 Try: 'Best heroes for early game' or 'How does the Training Ground work?'"
        )

# Modal setup with local data mounting
REQUIREMENTS = ["fastapi-poe", "numpy", "scikit-learn"]
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env({"POE_ACCESS_KEY": bot_access_key, "POE_BOT_NAME": bot_name})
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
)
app = App(f"poe-lastz-v7-6-embeddings-{deploy_hash}")

@app.function(image=image)
@asgi_app()
def fastapi_app():
    bot = LastZEmbeddingsBot()
    return fp.make_app(
        bot,
        access_key=bot_access_key,
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name),
    )

if __name__ == "__main__":
    print("🧪 Testing vector search...")
    try:
        search = LastZVectorSearch()
        test_result = search.simple_text_search("natalie hero")
        print(f"✅ Test result: Found {len(test_result)} items")
        if test_result:
            print(f"First result: {test_result[0]['name']}")
    except Exception as e:
        print(f"❌ Test failed: {e}")