"""
Last Z: Assistant V7.7 - True Vector Embeddings + Semantic Search
Implements real vector embeddings with sentence-transformers for semantic understanding.
"""

import hashlib
import json
import os
from collections.abc import AsyncIterable
from datetime import datetime
from typing import List, Dict, Any
import numpy as np

import fastapi_poe as fp
from modal import App, Image, asgi_app

# Generate hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%H:%M")

# Bot credentials
bot_access_key = "DjeSMuL0QwiwBSLa33Pa6t97kxhEmmXb"
bot_name = "LastZBetaV7"

class LastZVectorSearch:
    """True vector search using sentence-transformers embeddings"""
    
    def __init__(self):
        self.knowledge_items = []
        self.embeddings = None
        self.model = None
        self._load_model()
        self._load_all_data()
        self._create_embeddings()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            print("🤖 Loading sentence transformer model...")
            # Use a lightweight model suitable for Modal deployment
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.model = None
    
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
    
    def _create_embeddings(self):
        """Create embeddings for all knowledge items"""
        if not self.model or not self.knowledge_items:
            print("❌ Cannot create embeddings - model or data missing")
            return
        
        try:
            print("🧠 Creating embeddings for knowledge items...")
            texts = [item['text'] for item in self.knowledge_items]
            self.embeddings = self.model.encode(texts)
            print(f"✅ Created embeddings: {self.embeddings.shape}")
        except Exception as e:
            print(f"❌ Failed to create embeddings: {e}")
            self.embeddings = None
    
    def vector_search(self, query: str, min_similarity: float = 0.15) -> List[Dict[str, Any]]:
        """True vector search using semantic similarity - returns all relevant results above threshold"""
        if not self.model or self.embeddings is None:
            print("⚠️ Falling back to keyword search - embeddings not available")
            return self.simple_text_search(query)
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Create query embedding
            query_embedding = self.model.encode([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Get all results above threshold, sorted by relevance
            top_indices = np.argsort(similarities)[::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > min_similarity:  # Only include relevant results
                    item = self.knowledge_items[idx].copy()
                    item['similarity_score'] = float(similarities[idx])
                    results.append(item)
                else:
                    break  # Stop when similarity gets too low (since sorted)
            
            print(f"🔍 Vector search found {len(results)} results above {min_similarity} similarity")
            if results:
                print(f"Similarity range: {results[0]['similarity_score']:.3f} to {results[-1]['similarity_score']:.3f}")
            return results
            
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return self.simple_text_search(query, max_results)
    
    def simple_text_search(self, query: str) -> List[Dict[str, Any]]:
        """Fallback keyword-based search - returns all relevant matches"""
        print("📝 Using fallback keyword search")
        query_lower = query.lower()
        results = []
        
        for item in self.knowledge_items:
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
                item_copy = item.copy()
                item_copy['keyword_score'] = score
                results.append(item_copy)
        
        # Sort by score and return all relevant results
        results.sort(key=lambda x: x.get('keyword_score', 0), reverse=True)
        return results

# Global search instance
vector_search = LastZVectorSearch()

# Tool function that GPT can call
def search_lastz_knowledge(user_query: str) -> str:
    """
    Search Last Z game knowledge using semantic vector search.
    
    Args:
        user_query: Natural language question about Last Z game content
    
    Returns:
        JSON string with relevant game knowledge
    """
    try:
        print(f"🔧 Vector search tool called: '{user_query}'")
        
        if not vector_search.knowledge_items:
            return json.dumps({"error": "No knowledge data loaded"})
        
        # Perform vector search - let GPT decide how much info it needs
        results = vector_search.vector_search(user_query)
        
        if not results:
            return json.dumps({
                "query": user_query,
                "message": "No relevant matches found in knowledge base",
                "total_items": len(vector_search.knowledge_items),
                "search_method": "vector" if vector_search.embeddings is not None else "keyword"
            })
        
        # Format results
        formatted_results = []
        for item in results:
            result_item = {
                "type": item['type'],
                "name": item['name'],
                "summary": item['text'][:200] + "..." if len(item['text']) > 200 else item['text'],
                "full_data": item['data']
            }
            
            # Add similarity score if available
            if 'similarity_score' in item:
                result_item['similarity_score'] = item['similarity_score']
            elif 'keyword_score' in item:
                result_item['keyword_score'] = item['keyword_score']
            
            formatted_results.append(result_item)
        
        return json.dumps({
            "query": user_query,
            "results_count": len(formatted_results),
            "search_method": "vector" if vector_search.embeddings is not None else "keyword_fallback",
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
            "description": "Search Last Z game knowledge using semantic vector embeddings. Returns ALL semantically relevant content above similarity threshold - GPT will intelligently filter and summarize the most important information for the user's specific question. IMPORTANT: Always cite your sources by mentioning the specific item names and types from the search results (e.g., 'According to the hero data for Natalie...' or 'Based on the Training Ground building info...'). Include similarity scores when mentioning sources for transparency.",
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
        """Use vector semantic search to find relevant game knowledge"""
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
        
        # Stream with vector search tool calling
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
            introduction_message=f"Last Z Assistant V7.7 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🧠 TRUE VECTOR EMBEDDINGS with Semantic Search\n\n✅ AI-powered semantic understanding:\n• Heroes (roles, skills, strategies)\n• Buildings (scaling, synergies)\n• Equipment (optimal loadouts)\n\n🔍 Finds conceptually related information, not just keywords!\n🎯 Includes similarity scores for transparency\n\n💡 Try: 'Early game tank strategy' or 'Heroes that synergize with resource buildings'"
        )

# Modal setup with vector embeddings
REQUIREMENTS = ["fastapi-poe", "numpy", "scikit-learn", "sentence-transformers", "torch"]
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env({"POE_ACCESS_KEY": bot_access_key, "POE_BOT_NAME": bot_name})
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
)
app = App(f"poe-lastz-v7-7-vectors-{deploy_hash}")

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
    print("🧪 Testing vector embeddings search...")
    try:
        search = LastZVectorSearch()
        test_result = search.vector_search("best tank hero for early game")
        print(f"✅ Test result: Found {len(test_result)} items")
        if test_result:
            print(f"Top result: {test_result[0]['name']} (similarity: {test_result[0].get('similarity_score', 'N/A')})")
    except Exception as e:
        print(f"❌ Test failed: {e}")