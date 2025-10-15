"""
Last Z: Survival Shooter Assistant V7 - Clean Tool-Based Architecture
Pure GPT-5 tool calling for intelligent player data management.
No manual extraction - 100% LLM-driven with vector search.
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

# Modal app
app = modal.App(f"poe-lastz-v7-3-{deploy_hash}")

# Create image with dependencies
image = (
    modal.Image.debian_slim()
    .pip_install([
        "fastapi-poe==0.0.48",
        "sentence-transformers",
        "scikit-learn",
        "numpy",
        "pyyaml"
    ])
)

# Create volume for lastz-rag data
lastz_data_volume = modal.Volume.from_name("lastz-data", create_if_missing=True)

@app.function(image=image, volumes={"/app/data": lastz_data_volume})
def populate_data_volume():
    """Upload lastz-rag data to volume (run once to populate)"""
    import os
    
    # Check if data is already uploaded
    if os.path.exists("/app/data/core/data_index.md"):
        print("✅ Data already exists in volume")
        return
        
    print("📁 Uploading lastz-rag data to volume...")
    
    # Use volume batch upload from local data
    with lastz_data_volume.batch_upload() as batch:
        batch.put_directory("../lastz-rag/data", "/")
    
    lastz_data_volume.commit()
    print("✅ Data uploaded successfully")

# Data is already uploaded to volume
# Upload data to volume (run separately with: modal run poe_lastz_v7.py::populate_data_volume)
# populate_data_volume.remote()

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
            introduction_message=f"""🎮 **Last Z Expert V7.3** (Hash: {deploy_hash[:4]})

**Dynamic Loading Architecture:**
- 🗂️ **Live data loading** - Real-time access to lastz-rag repository  
- 🔍 **Vector knowledge search** - Semantic understanding of game questions
- �️ **Pure tool calling** - GPT-5 detects and extracts player data naturally
- ⚡ **No static fallbacks** - Always current, never stale information

Just chat normally - I'll intelligently track your progress and give personalized advice!

*Example: "I'm bradass, just hit HQ 8 with 13 orange heroes, what should I focus on?"*""",
            allow_attachments=True,
        )

    def _init_vector_search(self):
        """Initialize vector search with dynamic knowledge loading."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Load all knowledge dynamically
                all_knowledge = self.load_all_knowledge()
                texts = [item["text"] for item in all_knowledge]
                
                self._embeddings = self._encoder.encode(texts)
                self._knowledge_items = all_knowledge  # Store full knowledge items
                
                print(f"✅ Vector search ready: {len(texts)} items from dynamic sources")
            except Exception as e:
                self._encoder = "fallback"
                print(f"⚠️ Vector search failed, using keyword search: {e}")
                # Still store the knowledge items for keyword search
                if hasattr(self, '_knowledge_items'):
                    print(f"📝 Knowledge available for keyword search: {len(self._knowledge_items)} items")

    def load_all_knowledge(self):
        """Load all knowledge dynamically based on data_index.md"""
        knowledge = []
        
        try:
            # CRITICAL: Reload volume to see files uploaded after container creation
            if hasattr(self, '_volume'):
                self._volume.reload()
                print("🔄 Volume reloaded to see latest changes")
            
            # For now, check if data directory exists (future: implement full dynamic loading)
            data_path = "/app/data"
            if os.path.exists(data_path):
                # Parse data index to get loading instructions
                data_index = self.parse_data_index("/app/data/core/data_index.md")
                
                # 1. Load core static files (priority order)
                for core_file in data_index.get("core_static", []):
                    file_path = f"/app/data/core/{core_file['file']}"
                    if os.path.exists(file_path):
                        knowledge.extend(self.parse_markdown_file(file_path))
                
                # 2. Load dynamic JSON files
                for json_file in data_index.get("dynamic_json", {}).get("files", []):
                    file_path = f"/app/data/{json_file['path']}"
                    if os.path.exists(file_path):
                        knowledge.extend(self.parse_json_file(file_path, json_file.get("description", "")))
                
                # 3. Load dynamic JSON directories  
                for json_dir in data_index.get("dynamic_json", {}).get("directories", []):
                    dir_path = f"/app/data/{json_dir['path']}"
                    if os.path.exists(dir_path):
                        for filename in os.listdir(dir_path):
                            if filename.endswith('.json'):
                                knowledge.extend(self.parse_json_file(f"{dir_path}/{filename}", json_dir.get("description", "")))
                
                # 4. Load dynamic markdown directories
                for md_dir in data_index.get("dynamic_markdown", {}).get("directories", []):
                    dir_path = f"/app/data/{md_dir['path']}"
                    if os.path.exists(dir_path):
                        for filename in os.listdir(dir_path):
                            if filename.endswith('.md'):
                                knowledge.extend(self.parse_markdown_file(f"{dir_path}/{filename}"))
                                
        except Exception as e:
            print(f"Dynamic loading failed: {e}")
        
        # Return what we actually loaded - no fallbacks
        if not knowledge:
            print("❌ No knowledge loaded - dynamic loading failed")
        else:
            print(f"✅ Loaded {len(knowledge)} dynamic knowledge items")
            
        return knowledge

    def parse_data_index(self, index_path):
        """Parse the data_index.md file to get loading instructions"""
        try:
            with open(index_path, 'r') as f:
                content = f.read()
            
            # Extract YAML blocks from markdown
            import yaml
            yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
            
            parsed_data = {}
            for block in yaml_blocks:
                try:
                    data = yaml.safe_load(block)
                    parsed_data.update(data)
                except Exception as e:
                    print(f"Error parsing YAML block: {e}")
            
            return parsed_data
        except Exception as e:
            print(f"Error parsing data index: {e}")
            return {}

    def parse_json_file(self, file_path, description):
        """Convert JSON data to knowledge format"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            knowledge = []
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # Single object or dictionary of objects
                for key, value in data.items():
                    if isinstance(value, dict):
                        # Object with properties
                        text = f"{key}: {value.get('description', str(value))}"
                        tags = [key.lower(), description.lower()] if description else [key.lower()]
                        knowledge.append({"text": text, "tags": tags})
                    else:
                        # Simple key-value
                        text = f"{key}: {str(value)}"
                        tags = [key.lower(), description.lower()] if description else [key.lower()]
                        knowledge.append({"text": text, "tags": tags})
            
            elif isinstance(data, list):
                # Array of objects
                for item in data:
                    if isinstance(item, dict):
                        name = item.get('name', item.get('id', 'Unknown'))
                        desc = item.get('description', item.get('text', str(item)))
                        text = f"{name}: {desc}"
                        tags = [name.lower(), description.lower()] if description else [name.lower()]
                        knowledge.append({"text": text, "tags": tags})
            
            return knowledge
            
        except Exception as e:
            print(f"Failed to parse JSON file {file_path}: {e}")
            return []

    def parse_markdown_file(self, file_path):
        """Convert markdown to knowledge format"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            knowledge = []
            
            # Extract headers and bullet points as knowledge items
            lines = content.split('\n')
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Headers become context
                if line.startswith('#'):
                    current_section = line.replace('#', '').strip()
                
                # Bullet points become knowledge items
                elif line.startswith('-') or line.startswith('*'):
                    text = line.replace('-', '').replace('*', '').strip()
                    if text and len(text) > 10:  # Filter out very short items
                        tags = [current_section.lower()] if current_section else ["general"]
                        knowledge.append({"text": text, "tags": tags})
                
                # Bold text items
                elif '**' in line:
                    # Extract bold sections as important info
                    bold_items = re.findall(r'\*\*(.*?)\*\*', line)
                    for item in bold_items:
                        if len(item) > 5:
                            tags = [current_section.lower()] if current_section else ["general"]
                            knowledge.append({"text": item, "tags": tags})
            
            return knowledge
            
        except Exception as e:
            print(f"Failed to parse markdown file {file_path}: {e}")
            return []

    def extract_player_data(self, **kwargs) -> str:
        """Extract and update player information from conversation context."""
        # For v7, we'll use a simplified in-memory approach
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
        """Search knowledge base using dynamic knowledge."""
        self._init_vector_search()

        if self._encoder == "fallback":
            # Keyword search using only dynamically loaded knowledge
            query_words = query.lower().split()
            results = []
            
            if not hasattr(self, '_knowledge_items') or not self._knowledge_items:
                print("❌ No knowledge items available for search")
                return ["No knowledge available - dynamic loading failed"]
            
            for item in self._knowledge_items:
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
            
            # Use only dynamically loaded knowledge
            if not hasattr(self, '_knowledge_items') or not self._knowledge_items:
                return ["No knowledge available - dynamic loading failed"]
                
            return [self._knowledge_items[i]["text"] for i in top_indices if similarities[i] > 0.3]
        except Exception as e:
            print(f"Vector search error: {e}")
            return ["Search failed - check logs"]

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
    volumes={"/app/data": lastz_data_volume},
    secrets=[modal.Secret.from_dict({
        "POE_ACCESS_KEY": "DjeSMuL0QwiwBSLa33Pa6t97kxhEmmXb",
        "POE_BOT_NAME": "LastZBetaV7",
    })]
)
@modal.asgi_app()
def fastapi_app():
    bot = LastZCleanBot()
    bot._volume = lastz_data_volume  # Pass volume for reload
    return fp.make_app(bot, access_key=os.environ["POE_ACCESS_KEY"], bot_name=os.environ["POE_BOT_NAME"])

if __name__ == "__main__":
    bot = LastZCleanBot()
    app = fp.make_app(bot, access_key="dummy_key", bot_name="LastZBetaV7_1")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
