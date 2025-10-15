"""
Last Z: Survival Shooter Assistant V7 - Clean Tool-Based Architecture
Pure GPT-5 tool calling for intelligent player data management.
No manual extraction - 100% LLM-driven with vector search.
"""

import os
import json
import numpy as np
from datetime import datetime
from typing import Any, AsyncIterable, Dict, List
import hashlib

import fastapi_poe as fp
import modal

# Generate hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]

# Modal app
app = modal.App(f"poe-lastz-v7-clean-{deploy_hash}")

# Dependencies
image = modal.Image.debian_slim().pip_install([
    "fastapi-poe==0.0.48",
    "sentence-transformers",
    "numpy", 
    "scikit-learn",
])

# Last Z Knowledge Base
LASTZ_KNOWLEDGE = [
    {"text": "Headquarters level determines hero level cap at HQ × 5", "tags": ["hq", "hero", "level"]},
    {"text": "Training Ground produces EXP which cannot be purchased with gems", "tags": ["exp", "bottleneck"]},
    {"text": "Residence produces Zent which cannot be purchased with gems", "tags": ["zent", "bottleneck"]},
    {"text": "Orange heroes are S-rank: Sophia, Katrina, Evelyn, Oliveira, Mia", "tags": ["orange", "s-rank"]},
    {"text": "Purple heroes are A-rank: Fiona, Vivian, Christina, Leah, Ava, Selena, Maria, Isabella, Elizabeth, Miranda", "tags": ["purple"]},
    {"text": "Blue heroes are B-rank: Athena, William, Natalie, Angelina, Audrey, Giselle", "tags": ["blue"]},
    {"text": "Focus orange heroes first: Sophia (tank), Katrina (damage), Evelyn (support)", "tags": ["strategy", "orange"]},
    {"text": "Early game priority: HQ → Training Ground → Residence → Research", "tags": ["strategy", "early"]},
]

class LastZCleanBot(fp.PoeBot):
    """Clean tool-based Last Z assistant."""
    
    def __init__(self, access_key: str):
        super().__init__()
        self.access_key = access_key
        self._encoder = None
        self._embeddings = None

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        """Bot settings with clean tool definitions."""
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            introduction_message=f"""🎮 **Last Z Expert V7-Clean** (Hash: {deploy_hash[:4]})

**Pure Tool-Based Architecture:**
- 🧠 **Smart data extraction** - GPT-5 detects player info naturally
- 🔍 **Vector knowledge search** - Semantic understanding of game questions  
- 💾 **Persistent memory** - Remember your progress across conversations

Just chat normally - I'll intelligently track your progress and give personalized advice!

*Example: "I'm bradass, just hit HQ 8 with 13 orange heroes, what should I focus on?"*""",
            
            tool_executables=[
                {
                    "type": "function",
                    "function": {
                        "name": "update_player_profile",
                        "description": "Extract and store comprehensive player information when mentioned in conversation",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "account": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Gamertag/player name"},
                                        "level": {"type": "integer"},
                                        "power": {"type": "integer"},
                                        "alliance": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "rank": {"type": "string"}
                                            }
                                        }
                                    }
                                },
                                "progression": {
                                    "type": "object", 
                                    "properties": {
                                        "hq_level": {"type": "integer"},
                                        "exploration": {
                                            "type": "object",
                                            "properties": {
                                                "chapter": {"type": "integer"},
                                                "stage_cleared": {"type": "integer"}
                                            }
                                        }
                                    }
                                },
                                "resources": {
                                    "type": "object",
                                    "properties": {
                                        "food": {"type": "integer"},
                                        "wood": {"type": "integer"},
                                        "zent": {"type": "integer"},
                                        "diamonds": {"type": "integer"}
                                    }
                                },
                                "heroes": {
                                    "type": "object",
                                    "properties": {
                                        "roster_size": {"type": "integer"},
                                        "owned": {"type": "array", "items": {"type": "string"}},
                                        "highest_rarity": {"type": "string"}
                                    }
                                },
                                "buildings": {
                                    "type": "object",
                                    "properties": {
                                        "hq": {"type": "integer"},
                                        "training_ground": {"type": "integer"},
                                        "residence": {"type": "integer"}
                                    }
                                },
                                "meta": {
                                    "type": "object",
                                    "properties": {
                                        "days_played": {"type": "integer"},
                                        "vip_level": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        )

    def _init_vector_search(self):
        """Initialize vector search (lazy loading)."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                from sklearn.metrics.pairwise import cosine_similarity
                
                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                texts = [item["text"] for item in LASTZ_KNOWLEDGE]
                self._embeddings = self._encoder.encode(texts)
                print(f"✅ Vector search ready: {len(texts)} items")
            except:
                self._encoder = "fallback"
                print("⚠️ Using keyword fallback")

    def search_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        """Search knowledge base."""
        self._init_vector_search()
        
        if self._encoder == "fallback":
            # Simple keyword fallback
            query_words = query.lower().split()
            results = []
            for item in LASTZ_KNOWLEDGE:
                score = sum(1 for word in query_words if word in item["text"].lower())
                if score > 0:
                    results.append((score, item["text"]))
            results.sort(reverse=True)
            return [text for _, text in results[:top_k]]
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            query_embedding = self._encoder.encode([query])
            similarities = cosine_similarity(query_embedding, self._embeddings)[0]
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            return [LASTZ_KNOWLEDGE[i]["text"] for i in top_indices if similarities[i] > 0.3]
        except:
            return []

    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        """Main response handler."""
        
        # Handle tool calls
        if hasattr(request, 'tool_calls') and request.tool_calls:
            for tool_call in request.tool_calls:
                if tool_call.function.name == "update_player_profile":
                    args = json.loads(tool_call.function.arguments)
                    
                    # Load existing profile or create from template
                    try:
                        data_response = await fp.get_final_response(
                            fp.QueryRequest(
                                query=[fp.ProtocolMessage(role="user", content="get_profile")],
                                user_id=request.user_id,
                                conversation_id=request.conversation_id,
                            )
                        )
                        if hasattr(data_response, 'data') and data_response.data:
                            profile_data = json.loads(data_response.data)
                            profile = profile_data.get("player_profile", {})
                        else:
                            # Initialize with comprehensive template
                            template = {
                                "account": {"id": None, "name": None, "level": None, "power": None, "alliance": {"id": None, "name": None, "rank": None, "activity_level": None}},
                                "progression": {"hq_level": None, "exploration": {"chapter": None, "stage_cleared": None, "stars_total": None}, "reclaim_areas": [], "formations_unlocked": None, "troop_tier_unlocked": None, "research_progress": None},
                                "resources": {"food": None, "wood": None, "zent": None, "exp_items": None, "alloy": None, "energy": {"current": None, "max": None, "usage_focus": None}, "sweep_tickets": None, "diamonds": None},
                                "heroes": {"roster_size": None, "owned": [], "highest_rarity": None, "average_level": None, "star_distribution": {"1_star": None, "2_star": None, "3_star": None, "4_star": None, "5_star": None}, "roster": []},
                                "troops": {"assaulters": {"tier": None, "count": None}, "shooters": {"tier": None, "count": None}, "riders": {"tier": None, "count": None}, "training_focus": None},
                                "buildings": {"hq": None, "training_ground": None, "farmhouse": None, "lumberyard": None, "residence": None, "hospital": None, "laboratory": None, "club": None, "arena": None, "building_focus": None},
                                "social": {"friends": None, "recent_rallies": None, "pvp_rank_arena": None, "chat_channels_joined": [], "event_participation": None},
                                "meta": {"days_played": None, "login_streak": None, "vip_level": None, "spending_bracket": None},
                                "combat_stats": {"kill_points": None, "deaths": None}
                            }
                            profile = template
                    except:
                        # Initialize with comprehensive template on any error  
                        template = {
                            "account": {"id": None, "name": None, "level": None, "power": None, "alliance": {"id": None, "name": None, "rank": None, "activity_level": None}},
                            "progression": {"hq_level": None, "exploration": {"chapter": None, "stage_cleared": None, "stars_total": None}, "reclaim_areas": [], "formations_unlocked": None, "troop_tier_unlocked": None, "research_progress": None},
                            "resources": {"food": None, "wood": None, "zent": None, "exp_items": None, "alloy": None, "energy": {"current": None, "max": None, "usage_focus": None}, "sweep_tickets": None, "diamonds": None},
                            "heroes": {"roster_size": None, "owned": [], "highest_rarity": None, "average_level": None, "star_distribution": {"1_star": None, "2_star": None, "3_star": None, "4_star": None, "5_star": None}, "roster": []},
                            "troops": {"assaulters": {"tier": None, "count": None}, "shooters": {"tier": None, "count": None}, "riders": {"tier": None, "count": None}, "training_focus": None},
                            "buildings": {"hq": None, "training_ground": None, "farmhouse": None, "lumberyard": None, "residence": None, "hospital": None, "laboratory": None, "club": None, "arena": None, "building_focus": None},
                            "social": {"friends": None, "recent_rallies": None, "pvp_rank_arena": None, "chat_channels_joined": [], "event_participation": None},
                            "meta": {"days_played": None, "login_streak": None, "vip_level": None, "spending_bracket": None},
                            "combat_stats": {"kill_points": None, "deaths": None}
                        }
                        profile = template
                    
                    # Deep update profile with new data (only non-null values)
                    def deep_update(target, source):
                        for key, value in source.items():
                            if value is not None:
                                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                                    deep_update(target[key], value)
                                else:
                                    target[key] = value
                    
                    deep_update(profile, args)
                    
                    profile["last_updated"] = datetime.now().isoformat()
                    
                    # Store updated profile using DataResponse
                    try:
                        await fp.post_message_feedback(
                            message_id=request.conversation_id,
                            type=fp.FeedbackType.like,
                            feedback=fp.DataResponse(data=json.dumps({
                                "player_profile": profile,
                                "updated": datetime.now().isoformat()
                            }))
                        )
                        
                        # Format confirmation
                        updates = []
                        if args.get("account", {}).get("name"): 
                            updates.append(f"🎮 {args['account']['name']}")
                        if args.get("progression", {}).get("hq_level"): 
                            updates.append(f"🏰 HQ {args['progression']['hq_level']}")
                        if args.get("heroes", {}).get("roster_size"): 
                            updates.append(f"⚔️ {args['heroes']['roster_size']} heroes")
                        if args.get("account", {}).get("power"): 
                            updates.append(f"� {args['account']['power']:,} power")
                        
                        yield fp.PartialResponse(text=f"✅ **Profile Updated!** {' • '.join(updates) if updates else 'Data saved'}")
                        
                    except Exception as e:
                        yield fp.PartialResponse(text=f"⚠️ Profile update failed: {e}")
            return

        # Get user message
        user_message = request.query[-1].content
        
        # Search knowledge base
        relevant_knowledge = self.search_knowledge(user_message)
        
        # Load player profile context
        player_context = ""
        try:
            data_response = await fp.get_final_response(
                fp.QueryRequest(
                    query=[fp.ProtocolMessage(role="user", content="get_profile")],
                    user_id=request.user_id,
                    conversation_id=request.conversation_id,
                )
            )
            if hasattr(data_response, 'data') and data_response.data:
                profile_data = json.loads(data_response.data)
                profile = profile_data.get("player_profile", {})
                if profile:
                    context_parts = []
                    if profile.get("gamertag"): context_parts.append(f"Player: {profile['gamertag']}")
                    if profile.get("hq_level"): context_parts.append(f"HQ Level: {profile['hq_level']}")
                    hero_count = sum(profile.get(f"{color}_heroes", 0) for color in ["orange", "purple", "blue"])
                    if hero_count: context_parts.append(f"Total Heroes: {hero_count}")
                    
                    if context_parts:
                        player_context = f"**Player Context:** {' • '.join(context_parts)}\n\n"
        except:
            pass

        # Build enhanced system prompt
        knowledge_context = ""
        if relevant_knowledge:
            knowledge_context = "**Relevant Knowledge:**\n" + "\n".join(f"• {item}" for item in relevant_knowledge) + "\n\n"

        system_prompt = f"""You are a Last Z: Survival Shooter expert with access to tools.

{player_context}{knowledge_context}**Instructions:**
- Use the update_player_profile tool when players mention specific details (gamertag, levels, hero counts, etc.)
- Give personalized advice based on player context
- Focus on actionable strategies and priorities
- Keep responses concise but helpful"""

        # Create enhanced request
        enhanced_messages = [fp.ProtocolMessage(role="system", content=system_prompt)]
        enhanced_messages.extend(request.query)
        
        enhanced_request = fp.QueryRequest(
            query=enhanced_messages,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
        )
        
        # Stream response from GPT-5
        async for msg in fp.stream_request(enhanced_request, "GPT-5", enhanced_request):
            yield msg

@app.function(
    image=image,
    secrets=[modal.Secret.from_dict({
        "POE_ACCESS_KEY": os.getenv("POE_ACCESS_KEY", ""),
        "POE_BOT_NAME": "LastZCleanBot",
    })]
)
@modal.asgi_app()
def fastapi_app():
    bot = LastZCleanBot(os.environ["POE_ACCESS_KEY"])
    return fp.make_app(bot, access_key=os.environ["POE_ACCESS_KEY"], bot_name=os.environ["POE_BOT_NAME"])

if __name__ == "__main__":
    bot = LastZCleanBot("dummy_key")
    app = fp.make_app(bot, access_key="dummy_key", bot_name="LastZCleanBot")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)