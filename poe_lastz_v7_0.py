"""
Last Z: Survival Shooter Assistant V7 - Tool-Based Player Data Management
A Poe bot using vector search + intelligent tool calling for flexible player data extraction.
No hard-coded keywords - GPT-5 decides when and how to extract player information.
"""

import asyncio
import os
import json
import numpy as np
from datetime import datetime
from typing import Any, AsyncIterable, Dict, List, Optional
import hashlib

import fastapi_poe as fp
import modal

# Generate short hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]

# Create new Modal app instance for V7 Tools
app = modal.App(f"poe-lastz-v7-tools-{deploy_hash}")

# Configure Modal image with vector search dependencies
image = modal.Image.debian_slim().pip_install([
    "fastapi-poe==0.0.48",
    "sentence-transformers",  # 22MB semantic search model
    "numpy",                  # Vector operations
    "scikit-learn",          # Cosine similarity
])

# Embedded Last Z Knowledge Base with Vector Search
LASTZ_KNOWLEDGE_BASE = [
    # Buildings
    {"text": "Headquarters level determines hero level cap at HQ × 5", "category": "buildings", "tags": ["hq", "hero", "level", "cap"]},
    {"text": "Training Ground produces EXP which cannot be purchased with gems", "category": "buildings", "tags": ["exp", "training", "bottleneck"]},
    {"text": "Residence produces Zent which cannot be purchased with gems", "category": "buildings", "tags": ["zent", "residence", "bottleneck"]},
    {"text": "HQ level 1 to 2 costs 150 wood", "category": "upgrades", "tags": ["hq", "wood", "cost"]},
    {"text": "HQ level 2 to 3 costs 300 wood", "category": "upgrades", "tags": ["hq", "wood", "cost"]},
    {"text": "HQ level 3 to 4 costs 600 wood", "category": "upgrades", "tags": ["hq", "wood", "cost"]},
    
    # Heroes by rarity
    {"text": "Orange heroes are S-rank: Sophia, Katrina, Evelyn, Oliveira, Mia", "category": "heroes", "tags": ["orange", "s-rank", "best"]},
    {"text": "Purple heroes are A-rank: Fiona, Vivian, Christina, Leah, Ava, Selena, Maria, Isabella, Elizabeth, Miranda", "category": "heroes", "tags": ["purple", "a-rank"]},
    {"text": "Blue heroes are B-rank: Athena, William, Natalie, Angelina, Audrey, Giselle", "category": "heroes", "tags": ["blue", "b-rank"]},
    
    # Factions
    {"text": "Blood Rose faction heroes: Sophia, Oliveira, Natalie, Vivian, Christina, Ava, Miranda", "category": "heroes", "tags": ["blood rose", "faction"]},
    {"text": "Wings of Dawn faction heroes: Katrina, Mia, Fiona, Angelina, Audrey, Giselle", "category": "heroes", "tags": ["wings of dawn", "faction"]},
    {"text": "Guard of Order faction heroes: Evelyn, William, Leah, Elizabeth", "category": "heroes", "tags": ["guard of order", "faction"]},
    
    # Best strategies
    {"text": "Focus orange heroes first: Sophia (tank), Katrina (damage), Evelyn (support)", "category": "strategy", "tags": ["priority", "orange", "team"]},
    {"text": "Early game priority: HQ → Training Ground → Residence → Research", "category": "strategy", "tags": ["early", "building", "order"]},
    {"text": "EXP and Zent cannot be purchased - always the bottleneck resources", "category": "strategy", "tags": ["bottleneck", "exp", "zent"]},
    
    # Equipment
    {"text": "Equipment sets: Lightning (speed), Ice (defense), Fire (attack), Wind (critical)", "category": "equipment", "tags": ["sets", "bonuses"]},
    {"text": "Weapon upgrade priority: Orange heroes first, then purple supports", "category": "equipment", "tags": ["weapons", "priority"]},
    
    # Research
    {"text": "Economics research increases resource production efficiency", "category": "research", "tags": ["economics", "production"]},
    {"text": "Military research unlocks new troop types and combat bonuses", "category": "research", "tags": ["military", "troops"]},
    {"text": "Development research improves building efficiency and unlocks new structures", "category": "research", "tags": ["development", "buildings"]},
]

# Player Profile Data Structure
class PlayerProfile:
    def __init__(self, data: Dict = None):
        self.data = data or {}
        self.last_updated = datetime.now().isoformat()
    
    def update(self, new_data: Dict):
        """Update player profile with new information."""
        self.data.update(new_data)
        self.last_updated = datetime.now().isoformat()
        return self
    
    def get(self, key: str, default=None):
        return self.data.get(key, default)
    
    def to_dict(self):
        return {
            "profile": self.data,
            "last_updated": self.last_updated
        }

class LastZToolAssistant(fp.PoeBot):
    """Last Z assistant with vector search + intelligent tool-based player data management."""
    
    def __init__(self, access_key: str):
        super().__init__()
        self.access_key = access_key
        # Note: Sentence transformers will be loaded lazily to avoid startup delays
        self._encoder = None
        self._knowledge_embeddings = None

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        """Return bot settings with tool definitions for intelligent player data extraction."""
        deploy_time = datetime.now().strftime("%m/%d %H:%M")
        
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            allow_attachments=True,
            introduction_message=f"""🎮 **Last Z Strategy Expert V7 ({deploy_time})** - Hash: {deploy_hash[:4]}

I'm your Last Z: Survival Shooter expert with:
- 🔍 **Semantic knowledge search** - Find game info without exact keywords
- 🧠 **Intelligent player tracking** - I'll learn about your progress automatically
- 📊 **Personalized recommendations** - Tailored advice for your situation

**New in V7**: Tool-based player data management! I can intelligently detect and remember:
- Your gamertag and server
- Current HQ level and building progress  
- Hero collection and rarity counts
- Resource bottlenecks and priorities
- Long-term strategy goals

Just chat naturally about your game - I'll pick up relevant details automatically!

*Try: "I'm bradass on server 42, just hit HQ 8 with 13 orange heroes"*""",
            # Tool definitions for intelligent player data management
            tool_executables=[
                {
                    "type": "function",
                    "function": {
                        "name": "extract_player_data",
                        "description": "Extract and update player information from conversation context. Use when player mentions specific game details like gamertag, server, levels, hero counts, or progress updates.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "gamertag": {
                                    "type": "string",
                                    "description": "Player's in-game name or handle"
                                },
                                "server": {
                                    "type": "string", 
                                    "description": "Server number or name where player is active"
                                },
                                "hq_level": {
                                    "type": "integer",
                                    "description": "Current Headquarters building level"
                                },
                                "hero_counts": {
                                    "type": "object",
                                    "description": "Count of heroes by rarity",
                                    "properties": {
                                        "orange": {"type": "integer"},
                                        "purple": {"type": "integer"},
                                        "blue": {"type": "integer"}
                                    }
                                },
                                "building_levels": {
                                    "type": "object",
                                    "description": "Current building levels",
                                    "properties": {
                                        "training_ground": {"type": "integer"},
                                        "residence": {"type": "integer"},
                                        "research_lab": {"type": "integer"}
                                    }
                                },
                                "current_focus": {
                                    "type": "string",
                                    "description": "What the player is currently working on or prioritizing"
                                },
                                "bottlenecks": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Current resource or progression bottlenecks"
                                },
                                "notes": {
                                    "type": "string",
                                    "description": "Additional context or observations about player's situation"
                                }
                            }
                        }
                    }
                },
                {
                    "type": "function", 
                    "function": {
                        "name": "get_personalized_advice",
                        "description": "Generate personalized strategy advice based on player's current situation and progress. Use after extracting player data to provide tailored recommendations.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "advice_type": {
                                    "type": "string",
                                    "enum": ["building_priority", "hero_strategy", "resource_management", "team_composition", "next_steps"],
                                    "description": "Type of advice to generate"
                                },
                                "situation": {
                                    "type": "string",
                                    "description": "Player's current situation or specific question context"
                                }
                            },
                            "required": ["advice_type", "situation"]
                        }
                    }
                }
            ]
        )
    
    def _get_encoder_and_embeddings(self):
        """Lazy loading of sentence transformer and knowledge embeddings."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                from sklearn.metrics.pairwise import cosine_similarity
                
                # Load lightweight model (22MB)
                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Pre-compute knowledge base embeddings
                knowledge_texts = [item["text"] for item in LASTZ_KNOWLEDGE_BASE]
                self._knowledge_embeddings = self._encoder.encode(knowledge_texts)
                
                print(f"✅ Vector search initialized: {len(knowledge_texts)} knowledge items encoded")
            except ImportError:
                print("⚠️ sentence-transformers not available, falling back to keyword search")
                self._encoder = "fallback"
                self._knowledge_embeddings = None
        
        return self._encoder, self._knowledge_embeddings

    def semantic_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Perform semantic search on knowledge base."""
        encoder, embeddings = self._get_encoder_and_embeddings()
        
        # Fallback to keyword search if transformers unavailable
        if encoder == "fallback" or embeddings is None:
            return self._keyword_fallback_search(query, top_k)
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Encode query
            query_embedding = encoder.encode([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, embeddings)[0]
            
            # Get top-k most similar items
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Minimum similarity threshold
                    results.append({
                        **LASTZ_KNOWLEDGE_BASE[idx],
                        "similarity": float(similarities[idx])
                    })
            
            return results
            
        except Exception as e:
            print(f"Vector search error: {e}")
            return self._keyword_fallback_search(query, top_k)
    
    def _keyword_fallback_search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Fallback keyword-based search when vector search fails."""
        query_lower = query.lower()
        results = []
        
        for item in LASTZ_KNOWLEDGE_BASE:
            score = 0
            text_lower = item["text"].lower()
            
            # Check for exact word matches
            query_words = query_lower.split()
            for word in query_words:
                if word in text_lower:
                    score += 1
                if word in item.get("tags", []):
                    score += 2
            
            if score > 0:
                results.append({**item, "similarity": score / len(query_words)})
        
        # Sort by score and return top-k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    async def load_player_profile(self, request: fp.QueryRequest) -> PlayerProfile:
        """Load player profile from DataResponse or create new one."""
        try:
            # Try to load existing profile
            data_response = await fp.get_final_response(
                fp.QueryRequest(
                    query=[fp.ProtocolMessage(role="user", content="get_profile")],
                    user_id=request.user_id,
                    conversation_id=request.conversation_id,
                )
            )
            
            if hasattr(data_response, 'data') and data_response.data:
                profile_data = json.loads(data_response.data)
                return PlayerProfile(profile_data.get("profile", {}))
        except:
            pass  # Profile doesn't exist yet or error loading
        
        return PlayerProfile()  # Return empty profile

    async def save_player_profile(self, profile: PlayerProfile, request: fp.QueryRequest):
        """Save player profile using DataResponse."""
        try:
            # Save profile data
            await fp.post_message_feedback(
                message_id=request.conversation_id,  # Use conversation_id as message reference
                type=fp.FeedbackType.like,  # Required field
                feedback=fp.DataResponse(data=json.dumps(profile.to_dict()))
            )
        except Exception as e:
            print(f"Warning: Could not save player profile: {e}")

    async def handle_tool_call(self, tool_name: str, arguments: Dict, request: fp.QueryRequest) -> str:
        """Handle tool calls for player data management."""
        
        if tool_name == "extract_player_data":
            # Load existing profile
            profile = await self.load_player_profile(request)
            
            # Update with new data
            profile.update(arguments)
            
            # Save updated profile
            await self.save_player_profile(profile, request)
            
            # Format response
            summary_parts = []
            if arguments.get("gamertag"):
                summary_parts.append(f"🎮 Player: {arguments['gamertag']}")
            if arguments.get("server"):
                summary_parts.append(f"🌐 Server: {arguments['server']}")
            if arguments.get("hq_level"):
                summary_parts.append(f"🏰 HQ Level: {arguments['hq_level']}")
            if arguments.get("hero_counts"):
                hero_counts = arguments["hero_counts"]
                counts = [f"{color}: {count}" for color, count in hero_counts.items() if count]
                if counts:
                    summary_parts.append(f"⚔️ Heroes: {', '.join(counts)}")
            
            return f"✅ **Player Profile Updated!**\n\n{' • '.join(summary_parts)}\n\nI'll remember this information for future recommendations!"
        
        elif tool_name == "get_personalized_advice":
            # Load player profile for context
            profile = await self.load_player_profile(request)
            
            advice_type = arguments.get("advice_type", "next_steps")
            situation = arguments.get("situation", "")
            
            # Generate contextual advice based on profile
            profile_context = ""
            if profile.data:
                context_parts = []
                if profile.get("hq_level"):
                    context_parts.append(f"HQ Level {profile.get('hq_level')}")
                if profile.get("hero_counts"):
                    hero_counts = profile.get("hero_counts", {})
                    total_heroes = sum(hero_counts.values())
                    context_parts.append(f"{total_heroes} total heroes")
                if profile.get("current_focus"):
                    context_parts.append(f"Currently focusing on: {profile.get('current_focus')}")
                
                if context_parts:
                    profile_context = f"\n\n**Your Current Progress:** {' • '.join(context_parts)}"
            
            # Search knowledge base for relevant advice
            search_query = f"{advice_type} {situation}"
            knowledge_results = self.semantic_search(search_query, top_k=3)
            
            advice_content = ""
            if knowledge_results:
                advice_content = "\n\n**📚 Relevant Knowledge:**\n"
                for i, result in enumerate(knowledge_results, 1):
                    advice_content += f"{i}. {result['text']}\n"
            
            return f"🎯 **{advice_type.replace('_', ' ').title()} Advice**{profile_context}{advice_content}"
        
        return f"Tool '{tool_name}' executed with arguments: {arguments}"

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """Main response handler with intelligent tool calling."""
        
        # Get the user's message
        last_message = request.query[-1].content
        
        # Sanitize text to prevent encoding errors
        def sanitize_text(text: str) -> str:
            """Replace problematic unicode characters to prevent encoding errors."""
            replacements = {
                ''': "'", ''': "'", '"': '"', '"': '"',
                '—': '--', '–': '-', '…': '...',
                '×': 'x', '°': ' degrees',
            }
            for unicode_char, replacement in replacements.items():
                text = text.replace(unicode_char, replacement)
            # Convert any remaining non-ASCII to ASCII approximation
            return text.encode('ascii', 'ignore').decode('ascii')
        
        sanitized_message = sanitize_text(last_message)
        
        # Check if this is a tool call
        if hasattr(request, 'tool_calls') and request.tool_calls:
            for tool_call in request.tool_calls:
                tool_result = await self.handle_tool_call(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                    request
                )
                yield fp.PartialResponse(text=tool_result)
            return
        
        # Search knowledge base for relevant information
        knowledge_results = self.semantic_search(sanitized_message, top_k=3)
        
        # Build enhanced context with knowledge and player profile
        profile = await self.load_player_profile(request)
        
        # Create enhanced query with system context
        enhanced_messages = [
            fp.ProtocolMessage(
                role="system", 
                content=f"""You are a Last Z: Survival Shooter expert with access to tools for intelligent player data management.

IMPORTANT TOOL USAGE:
- When players mention specific game details (gamertag, server, levels, hero counts, building progress), ALWAYS call extract_player_data tool
- When giving advice, consider calling get_personalized_advice tool for context-aware recommendations  
- Use tools proactively to enhance player experience

Player Profile Context: {json.dumps(profile.data) if profile.data else "No profile data yet"}

Current Knowledge Base Results:
{chr(10).join([f"- {result['text']}" for result in knowledge_results]) if knowledge_results else "No relevant knowledge found"}

Provide expert guidance while using tools intelligently to remember player details and give personalized advice."""
            )
        ]
        
        # Add conversation history
        for message in request.query:
            enhanced_messages.append(fp.ProtocolMessage(
                role=message.role,
                content=sanitize_text(message.content)
            ))
        
        # Create enhanced request
        enhanced_request = fp.QueryRequest(
            query=enhanced_messages,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
        )
        
        # Stream response from GPT-5 with tool capabilities
        async for msg in fp.stream_request(enhanced_request, "GPT-5", enhanced_request):
            yield msg

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_dict({
            "POE_ACCESS_KEY": os.getenv("POE_ACCESS_KEY", ""),
            "POE_BOT_NAME": "LastZToolBot",
        })
    ],
)
@modal.asgi_app()
def fastapi_app():
    bot = LastZToolAssistant(os.environ["POE_ACCESS_KEY"])
    
    # Use fp.make_app instead of deprecated fp.make_app
    app = fp.make_app(bot, access_key=os.environ["POE_ACCESS_KEY"], bot_name=os.environ["POE_BOT_NAME"])
    
    return app

if __name__ == "__main__":
    # For local development
    import uvicorn
    bot = LastZToolAssistant("dummy_key")
    app = fp.make_app(bot, access_key="dummy_key", bot_name="LastZToolBot")
    uvicorn.run(app, host="0.0.0.0", port=8000)