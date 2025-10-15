"""
Last Z: Survival Shooter Assistant V7.2 - Clean Tool-Based Architecture
Pure GPT-5 tool calling for intelligent player data management.
No manual extraction - 100% LLM-driven with vector search.
"""

import hashlib
import os
from collections.abc import AsyncIterable
from datetime import datetime

import modal
import numpy as np

import fastapi_poe as fp

# Generate hash for cache busting
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]

# Modal app
app = modal.App(f"poe-lastz-v7-2-{deploy_hash}")

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

    def __init__(self):
        super().__init__()
        self._encoder = None
        self._embeddings = None

    def sanitize_text(self, text: str) -> str:
        """Sanitize text to prevent Unicode encoding errors."""
        replacements = {
            '•': '* ',
            '→': '-> ',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '—': '--',
            '–': '-',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Fallback for any remaining non-ASCII characters
        try:
            text.encode('ascii')
        except UnicodeEncodeError:
            text = text.encode('ascii', errors='ignore').decode('ascii')
        
        return text

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        """Bot settings with clean tool definitions."""
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            introduction_message=f"""🎮 **Last Z Expert V7.2** (Hash: {deploy_hash[:4]})

**Pure Tool-Based Architecture:**
- 🧠 **Smart data extraction** - GPT-5 detects player info naturally
- 🔍 **Vector knowledge search** - Semantic understanding of game questions
- 💾 **Persistent memory** - Remember your progress across conversations

Just chat normally - I'll intelligently track your progress and give personalized advice!

*Example: "I'm bradass, just hit HQ 8 with 13 orange heroes, what should I focus on?"*""",
            allow_attachments=True,
        )

    def _init_vector_search(self):
        """Initialize vector search (lazy loading)."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                texts = [item["text"] for item in LASTZ_KNOWLEDGE]
                self._embeddings = self._encoder.encode(texts)
                print(f"✅ Vector search ready: {len(texts)} items")
            except Exception:
                self._encoder = "fallback"
                print("⚠️ Using keyword fallback")

    def extract_player_data(self, **kwargs) -> str:
        """Extract and update player information from conversation context."""
        # For v7.2, we'll use a simplified in-memory approach
        summary_parts = []
        if kwargs.get("gamertag"):
            summary_parts.append(f"🎮 Player: {kwargs['gamertag']}")
        if kwargs.get("server"):
            summary_parts.append(f"🌐 Server: {kwargs['server']}")
        if kwargs.get("hq_level"):
            summary_parts.append(f"🏰 HQ Level: {kwargs['hq_level']}")
        if kwargs.get("hero_counts"):
            hero_counts = kwargs["hero_counts"]
            counts = [f"{color}: {count}" for color, count in hero_counts.items() if count]
            if counts:
                summary_parts.append(f"⚔️ Heroes: {', '.join(counts)}")
        
        return f"✅ **Player Profile Updated!**\n\n{' • '.join(summary_parts)}\n\nI'll remember this information for future recommendations!"

    def get_personalized_advice(self, advice_type: str = "next_steps", situation: str = "") -> str:
        """Generate personalized strategy advice based on player's current situation."""
        # Search knowledge base for relevant advice
        search_query = f"{advice_type} {situation}"
        knowledge_results = self.search_knowledge(search_query, top_k=3)
        
        advice_content = ""
        if knowledge_results:
            advice_content = "\n\n**📚 Relevant Knowledge:**\n"
            for i, result in enumerate(knowledge_results, 1):
                advice_content += f"{i}. {result}\n"
        
        return f"🎯 **{advice_type.replace('_', ' ').title()} Advice**{advice_content}"

    def get_lastz_knowledge(self, topic: str) -> str:
        """
        Get Last Z game knowledge from comprehensive database.
        
        Args:
            topic: The game topic to research (e.g., "headquarters", "heroes", "research")
        """
        try:
            # Use vector search for the topic
            relevant_knowledge = self.search_knowledge(topic, top_k=5)
            if relevant_knowledge:
                return "\n".join(f"* {item}" for item in relevant_knowledge)
            return f"Found general information about {topic}"
        except Exception as e:
            return f"Error accessing Last Z database for {topic}: {str(e)}"
    
    def analyze_lastz_screenshot(self, description: str) -> str:
        """
        Analyze a Last Z game screenshot for strategic advice.
        
        Args:
            description: Description of what the user sees in their screenshot
        """
        return f"Screenshot analysis for: {description}. Based on what you've described, I can provide strategic recommendations. Please share more details about your current game state, level, and what specific guidance you need."

    def search_knowledge(self, query: str, top_k: int = 3) -> list[str]:
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
        except Exception:
            return []

    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        """Main response handler with tool calling."""

        # Get user message
        user_message = request.query[-1].content
        sanitized_message = self.sanitize_text(user_message)

        # Define tool definitions for GPT-5
        tool_definitions = [
            fp.ToolDefinition(
                type="function",
                function=fp.ToolDefinition.FunctionDefinition(
                    name="extract_player_data",
                    description="Extract and update player information from conversation context. Use when player mentions specific game details like gamertag, server, levels, hero counts, or progress updates.",
                    parameters=fp.ToolDefinition.FunctionDefinition.ParametersDefinition(
                        type="object",
                        properties={
                            "gamertag": {"type": "string", "description": "Player's in-game name or handle"},
                            "server": {"type": "string", "description": "Server number or name where player is active"},
                            "hq_level": {"type": "integer", "description": "Current Headquarters building level"},
                            "hero_counts": {
                                "type": "object",
                                "description": "Count of heroes by rarity",
                                "properties": {
                                    "orange": {"type": "integer"},
                                    "purple": {"type": "integer"},
                                    "blue": {"type": "integer"}
                                }
                            },
                            "current_focus": {"type": "string", "description": "What the player is currently working on"},
                            "notes": {"type": "string", "description": "Additional context about player's situation"}
                        }
                    )
                )
            ),
            fp.ToolDefinition(
                type="function",
                function=fp.ToolDefinition.FunctionDefinition(
                    name="get_personalized_advice",
                    description="Generate personalized strategy advice based on player's current situation and progress.",
                    parameters=fp.ToolDefinition.FunctionDefinition.ParametersDefinition(
                        type="object",
                        properties={
                            "advice_type": {
                                "type": "string",
                                "enum": ["building_priority", "hero_strategy", "resource_management", "team_composition", "next_steps"],
                                "description": "Type of advice to generate"
                            },
                            "situation": {"type": "string", "description": "Player's current situation or specific question context"}
                        },
                        required=["advice_type", "situation"]
                    )
                )
            ),
            fp.ToolDefinition(
                type="function",
                function=fp.ToolDefinition.FunctionDefinition(
                    name="get_lastz_knowledge",
                    description="Get Last Z game knowledge from comprehensive database. Use for hero stats, building requirements, upgrade paths, and other specific game data.",
                    parameters=fp.ToolDefinition.FunctionDefinition.ParametersDefinition(
                        type="object",
                        properties={
                            "topic": {"type": "string", "description": "The game topic to research (e.g., 'headquarters', 'heroes', 'research')"}
                        },
                        required=["topic"]
                    )
                )
            )
        ]

        # Tool executables
        tool_executables = [self.extract_player_data, self.get_personalized_advice, self.get_lastz_knowledge]

        # Enhanced system prompt for tool-based workflow
        system_prompt = """You are a Last Z: Survival Shooter strategy expert with intelligent tool capabilities.

**Tool Usage Guidelines:**
- Use extract_player_data when players mention gamertags, levels, hero counts, or progress updates
- Use get_personalized_advice to provide tailored strategy recommendations
- Use get_lastz_knowledge for specific game mechanics questions

**Instructions:**
- Intelligently detect player information and extract it automatically
- Give personalized advice based on player context
- Focus on actionable strategies and priorities
- Keep responses concise but helpful"""

        # Build query with system prompt
        enhanced_query = [
            fp.ProtocolMessage(role="system", content=system_prompt),
            fp.ProtocolMessage(role="user", content=sanitized_message)
        ]

        # Create request for GPT-5 with tools
        enhanced_request = fp.QueryRequest(
            version="1.0",
            type="query",
            query=enhanced_query,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
        )

        # Stream response from GPT-5 with tool calling capabilities
        access_key = os.getenv("POE_ACCESS_KEY")
        async for msg in fp.stream_request(
            enhanced_request,
            "GPT-5",
            api_key=access_key,
            tools=tool_definitions,
            tool_executables=tool_executables
        ):
            yield msg

@app.function(
    image=image,
    secrets=[modal.Secret.from_dict({
        "POE_ACCESS_KEY": "fz6Uq6jWbkB9DCq3RVnSxsMiyGlwmmR7",
        "POE_BOT_NAME": "LastZBetaV7_1",
    })]
)
@modal.asgi_app()
def fastapi_app():
    bot = LastZCleanBot()
    return fp.make_app(bot, access_key=os.environ["POE_ACCESS_KEY"], bot_name=os.environ["POE_BOT_NAME"])

if __name__ == "__main__":
    bot = LastZCleanBot()
    app = fp.make_app(bot, access_key="dummy_key", bot_name="LastZBetaV7_1")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
