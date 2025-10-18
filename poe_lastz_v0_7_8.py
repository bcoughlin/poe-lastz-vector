"""
Last Z: Assistant v0.7.8 - Vector Embeddings + Image Analysis
Adds multi-modal capabilities for analyzing LastZ game screenshots.
"""

import hashlib
import json
import os
import re
from datetime import datetime

from modal import App, Image, asgi_app

import fastapi_poe as fp

# Generate hash for cache busting
deploy_hash = hashlib.md5(
    str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%m%d%H%M")

# Bot credentials
bot_access_key = "QxXYsepAwwQJg7kIOpTAf0mD9kTpvknZ"
bot_name = "LastzAiBeta"


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
            self.model = SentenceTransformer(
                'all-MiniLM-L6-v2')  # type: ignore
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.model = None

    def _load_all_data(self):
        """Load and process all data using data_index.md configuration"""
        data_path = "/app/data"
        if not os.path.exists(data_path):
            print("❌ Data path not found")
            return

        print(f"🔍 Loading data from {data_path}")

        # Load configuration from data_index.md
        index_config = self._parse_data_index(data_path)

        if index_config:
            # Load based on configuration
            self._load_from_config(data_path, index_config)
        else:
            # Fallback to legacy hardcoded loading
            print("⚠️ Using fallback loading - data_index.md not found or invalid")
            self._load_legacy_hardcoded(data_path)

        print(f"✅ Loaded {len(self.knowledge_items)} knowledge items")

    def _parse_data_index(self, data_path):
        """Parse data_index.md to get loading configuration"""
        index_path = f"{data_path}/data_index.md"
        if not os.path.exists(index_path):
            return None

        try:
            with open(index_path, encoding='utf-8') as f:
                content = f.read()

            # Simple parser for the YAML-like structure in the markdown
            config = {
                'core_static': [],
                'dynamic_json_dirs': [],
                'dynamic_json_files': [],
                'dynamic_markdown_dirs': []
            }

            current_section = None

            for line in content.split('\n'):
                line = line.strip()

                # Detect sections
                if 'core_static:' in line:
                    current_section = 'core_static'
                elif 'directories:' in line and 'dynamic_json' in content[:content.index(line)]:
                    current_section = 'json_dirs'
                elif 'files:' in line and 'dynamic_json' in content[:content.index(line)]:
                    current_section = 'json_files'
                elif 'directories:' in line and 'dynamic_markdown' in content[:content.index(line)]:
                    current_section = 'markdown_dirs'

                # Parse file entries
                elif line.startswith('- file:') and current_section == 'core_static':
                    # Extract filename from: - file: "core/game_fundamentals.md"
                    if '"' in line:
                        filename = line.split('"')[1]
                        config['core_static'].append(filename)

                elif line.startswith('- path:') and current_section == 'json_dirs':
                    # Extract path from: - path: "heroes/"
                    if '"' in line:
                        path = line.split('"')[1].rstrip('/')
                        config['dynamic_json_dirs'].append(path)

                elif line.startswith('- path:') and current_section == 'json_files':
                    # Extract path from: - path: "buildings.json"
                    if '"' in line:
                        filename = line.split('"')[1]
                        config['dynamic_json_files'].append(filename)

                elif line.startswith('- path:') and current_section == 'markdown_dirs':
                    # Extract path from: - path: "kb/"
                    if '"' in line:
                        path = line.split('"')[1].rstrip('/')
                        config['dynamic_markdown_dirs'].append(path)

            print(
                f"📋 Parsed data_index.md: {len(config['core_static'])} core files, {len(config['dynamic_json_dirs'])} JSON dirs, {len(config['dynamic_json_files'])} JSON files")
            return config

        except Exception as e:
            print(f"❌ Error parsing data_index.md: {e}")
            return None

    def _load_from_config(self, data_path, config):
        """Load data based on data_index.md configuration"""

        # Load core static markdown files
        for filepath in config['core_static']:
            full_path = f"{data_path}/{filepath}"
            if os.path.exists(full_path):
                try:
                    with open(full_path, encoding='utf-8') as f:
                        content = f.read()

                    filename = os.path.basename(filepath)
                    searchable_text = f"Core Guide: {filename.replace('.md', '').replace('_', ' ').title()} "
                    searchable_text += f"Content: {content[:500]}..."

                    self.knowledge_items.append({
                        'type': 'core_guide',
                        'name': filename.replace('.md', '').replace('_', ' ').title(),
                        'text': searchable_text,
                        'data': {'filename': filename, 'content': content}
                    })
                    print(f"✅ Loaded core guide: {filepath}")
                except Exception as e:
                    print(f"❌ Error loading {filepath}: {e}")

        # Load dynamic JSON directories
        for dir_path in config['dynamic_json_dirs']:
            full_dir_path = f"{data_path}/{dir_path}"
            if os.path.exists(full_dir_path):
                self._load_json_directory(full_dir_path, dir_path)

        # Load dynamic JSON files
        for filename in config['dynamic_json_files']:
            filepath = f"{data_path}/{filename}"
            if os.path.exists(filepath):
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    self._process_json_file(filename, data)
                    print(f"✅ Loaded JSON file: {filename}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")

        # Load dynamic markdown directories
        for dir_path in config['dynamic_markdown_dirs']:
            full_dir_path = f"{data_path}/{dir_path}"
            if os.path.exists(full_dir_path):
                self._load_markdown_directory(full_dir_path, dir_path)

    def _load_json_directory(self, dir_path, dir_name):
        """Load all JSON files from a directory"""
        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                try:
                    with open(f"{dir_path}/{filename}") as f:
                        data = json.load(f)

                    if dir_name == 'heroes':
                        self._process_hero_file(filename, data)
                    elif dir_name == 'research':
                        self._process_research_file(filename, data)
                    else:
                        self._process_generic_json(filename, data, dir_name)

                except Exception as e:
                    print(f"Error loading {dir_name}/{filename}: {e}")

    def _load_markdown_directory(self, dir_path, dir_name):
        """Load all markdown files from a directory"""
        for filename in os.listdir(dir_path):
            if filename.endswith('.md'):
                try:
                    with open(f"{dir_path}/{filename}", encoding='utf-8') as f:
                        content = f.read()

                    searchable_text = f"{dir_name.upper()} Article: {filename.replace('.md', '').replace('_', ' ').title()} "
                    searchable_text += f"Content: {content[:500]}..."

                    self.knowledge_items.append({
                        'type': f'{dir_name}_article',
                        'name': filename.replace('.md', '').replace('_', ' ').title(),
                        'text': searchable_text,
                        'data': {'filename': filename, 'content': content, 'directory': dir_name}
                    })
                    print(f"✅ Loaded {dir_name} article: {filename}")
                except Exception as e:
                    print(f"❌ Error loading {dir_name}/{filename}: {e}")

    def _process_hero_file(self, filename, hero_data):
        """Process hero JSON files"""
        hero_text = f"Hero: {hero_data.get('name', 'Unknown')} "
        hero_text += f"Role: {hero_data.get('role', 'Unknown')} "
        hero_text += f"Rarity: {hero_data.get('rarity', 'Unknown')} "
        if 'skills' in hero_data:
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
            'name': hero_data.get('name', filename),
            'text': hero_text,
            'data': hero_data
        })

    def _process_research_file(self, filename, research_data):
        """Process research JSON files"""
        research_text = f"Research: {research_data.get('name', filename)} "
        research_text += f"Category: {research_data.get('category', 'Unknown')} "
        research_text += f"Description: {research_data.get('description', '')}"

        self.knowledge_items.append({
            'type': 'research',
            'name': research_data.get('name', filename),
            'text': research_text,
            'data': research_data
        })

    def _process_generic_json(self, filename, data, directory):
        """Process generic JSON files from directories"""
        content_text = f"{directory.title()} Data: {filename} "
        content_text += f"File containing {len(str(data))} characters of {directory} information"

        self.knowledge_items.append({
            'type': directory,
            'name': filename.replace('.json', '').replace('_', ' ').title(),
            'text': content_text,
            'data': data
        })

    def _load_legacy_hardcoded(self, data_path):
        """Fallback to hardcoded loading if data_index.md fails"""
        print("🔄 Using legacy hardcoded data loading...")

        # Legacy core files
        core_files = ["game_fundamentals.md",
                      "terminology.md", "what_is_lastz.md", "README.md"]
        core_path = f"{data_path}/core"

        if os.path.exists(core_path):
            for filename in core_files:
                filepath = f"{core_path}/{filename}"
                if os.path.exists(filepath):
                    try:
                        with open(filepath, encoding='utf-8') as f:
                            content = f.read()

                        searchable_text = f"Core Guide: {filename.replace('.md', '').replace('_', ' ').title()} "
                        searchable_text += f"Content: {content[:500]}..."

                        self.knowledge_items.append({
                            'type': 'core_guide',
                            'name': filename.replace('.md', '').replace('_', ' ').title(),
                            'text': searchable_text,
                            'data': {'filename': filename, 'content': content}
                        })
                    except Exception as e:
                        print(f"❌ Error loading {filename}: {e}")

        # Legacy directory scans
        for directory in ['heroes', 'research']:
            dir_path = f"{data_path}/{directory}"
            if os.path.exists(dir_path):
                self._load_json_directory(dir_path, directory)

    def _process_json_file(self, filename, data):
        """Process different types of JSON files"""
        file_type = filename.replace('.json', '')

        if filename == 'buildings.json' and 'buildings' in data:
            for building in data['buildings']:
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

        elif filename == 'equipment.json':
            # Handle different possible structures
            equipment_items = []
            if isinstance(data, list):
                equipment_items = data
            elif 'equipment' in data and isinstance(data['equipment'], list):
                equipment_items = data['equipment']
            elif 'items' in data and isinstance(data['items'], list):
                equipment_items = data['items']

            for item in equipment_items[:20]:  # Increased limit
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

        else:
            # Generic handler for other JSON files
            content_text = f"{file_type.replace('_', ' ').title()}: "
            content_text += f"File data containing {len(str(data))} characters of game information"

            self.knowledge_items.append({
                'type': file_type,
                'name': file_type.replace('_', ' ').title(),
                'text': content_text,
                'data': data
            })

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

    def vector_search(self, query, min_similarity=0.20):
        """True vector search using semantic similarity - optimized for performance"""
        if not self.model or self.embeddings is None:
            print("⚠️ Falling back to keyword search - embeddings not available")
            return self.simple_text_search(query)

        try:
            import time

            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

            start_time = time.time()

            # Create query embedding
            query_embedding = self.model.encode([query])

            # Calculate similarities
            similarities = cosine_similarity(
                query_embedding, self.embeddings)[0]

            # Get all results above threshold, sorted by relevance
            # Use numpy for faster processing
            relevant_indices = np.where(similarities > min_similarity)[0]
            relevant_similarities = similarities[relevant_indices]

            # Sort by similarity (descending)
            sorted_indices = relevant_indices[np.argsort(
                relevant_similarities)[::-1]]

            results = []
            for idx in sorted_indices:
                item = self.knowledge_items[idx].copy()
                item['similarity_score'] = float(similarities[idx])
                results.append(item)

            search_time = time.time() - start_time
            print(
                f"⚡ Vector search: {len(results)} results in {search_time:.2f}s (similarity {min_similarity}+)")
            if results:
                print(
                    f"Top similarity: {results[0]['similarity_score']:.3f}, Lowest: {results[-1]['similarity_score']:.3f}")
            return results

        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return self.simple_text_search(query)

    def simple_text_search(self, query):
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

# Debug tracking for hallucination detection
debug_tracker = {
    "tools_called": [],
    "results_returned": 0,
    "last_query": ""
}

# NEW v0.7.8: Image analysis tool


def analyze_lastz_screenshot(image_description, user_query):
    """
    Analyze LastZ game screenshots for strategic advice.

    Args:
        image_description: Poe's automated image analysis description
        user_query: User's question about the image

    Returns:
        JSON string with visual analysis and strategic recommendations
    """
    try:
        print(f"🖼️ Image analysis tool called: '{user_query}' with image")

        # Track tool usage for debug
        debug_tracker["tools_called"].append("analyze_lastz_screenshot")
        debug_tracker["last_query"] = user_query

        # Do vector search based on user query to get relevant knowledge
        combined_query = f"{user_query} {image_description}"
        knowledge_results = vector_search.vector_search(combined_query)

        # Limit results for point efficiency - top 3 most relevant only
        knowledge_results = knowledge_results[:3]
        # Create citations from knowledge search
        debug_tracker["results_returned"] = len(knowledge_results)
        citations = []
        for item in knowledge_results:  # Use all limited results
            score = item.get('similarity_score', item.get('keyword_score', 0))
            # Use actual filename instead of friendly title
            filename = item.get('data', {}).get('filename', item['name'])
            citations.append(f"{filename} ({item['type']}, {score:.3f})")

        citation_text = "\n\n---\nSources: " + \
            " • ".join(citations) if citations else ""

        # Return the raw data for GPT to analyze
        return json.dumps({
            "image_description": image_description,
            "user_query": user_query,
            "knowledge_results": knowledge_results,
            "citations": citation_text,
            "analysis_type": "screenshot_with_knowledge",
            "debug_citations": citation_text
        }, indent=2)

    except Exception as e:
        print(f"❌ Image analysis error: {e}")
        return json.dumps({"error": str(e)})


def load_prompt_file(filename):
    """Load system prompt from file - mirrors data loading approach"""
    try:
        # Mirror the data loading approach - try /app/prompts first (Modal mount)
        paths_to_try = [
            f"/app/prompts/{filename}",  # Modal mount path (like /app/data)
            f"/root/prompts/{filename}",  # Modal container runtime path
            os.path.join(os.path.dirname(__file__), "prompts",
                         filename),  # Relative to script
            os.path.join("prompts", filename),  # Current working directory
        ]

        for prompt_path in paths_to_try:
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    print(f"✅ Loaded prompt from: {prompt_path}")
                    return content

        print(f"❌ Prompt file {filename} not found in any expected location")
        print(f"🔍 Tried paths: {paths_to_try}")

        # Use embedded fallback with proper instructions
        return """You are a Last Z strategy expert.
KEEP RESPONSES BRIEF AND POINT-EFFICIENT - users have limited daily budgets.
ALWAYS use search_lastz_knowledge for questions about heroes, buildings, strategy, or game mechanics.
ALWAYS use analyze_lastz_screenshot for images.
ONLY cite sources from your tool search results."""

    except Exception as e:
        print(f"⚠️ Failed to load prompt file {filename}: {e}")
        return "You are a Last Z strategy expert. Keep responses brief and helpful."


# Load single unified prompt at import time
SYSTEM_PROMPT = load_prompt_file("system_prompt.md")


# Tool function that GPT can call for regular knowledge search


def search_lastz_knowledge(user_query):
    """
    Search Last Z game knowledge using semantic vector search.

    Args:
        user_query: Natural language question about Last Z game content

    Returns:
        JSON string with relevant game knowledge
    """
    try:
        print(f"🔧 Vector search tool called: '{user_query}'")

        # Track tool usage for debug
        debug_tracker["tools_called"].append("search_lastz_knowledge")
        debug_tracker["last_query"] = user_query

        if not vector_search.knowledge_items:
            debug_tracker["results_returned"] = 0
            return json.dumps({"error": "No knowledge data loaded"})

        # Perform optimized vector search
        results = vector_search.vector_search(user_query)

        # Smart result limiting for point efficiency
        if len(results) > 3:
            print(
                f"📊 Large result set ({len(results)}), limiting to top 3 for point efficiency")
            results = results[:3]

        debug_tracker["results_returned"] = len(results)

        if not results:
            return json.dumps({
                "query": user_query,
                "message": "No relevant matches found in knowledge base",
                "total_items": len(vector_search.knowledge_items),
                "search_method": "vector" if vector_search.embeddings is not None else "keyword"
            })

        # Format results with clean structure
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

        # Create debug citations - limit for point efficiency
        citations = []
        for item in results:  # Use all limited results (max 3)
            score = item.get('similarity_score', item.get('keyword_score', 0))
            # Use actual filename instead of friendly title
            filename = item.get('data', {}).get('filename', item['name'])
            citations.append(f"{filename} ({item['type']}, {score:.3f})")

        citation_text = "\n\n---\nSources: " + " • ".join(citations)

        return json.dumps({
            "query": user_query,
            "results_count": len(formatted_results),
            "search_method": "vector" if vector_search.embeddings is not None else "keyword_fallback",
            "results": formatted_results,
            "debug_citations": citation_text
        }, indent=2)

    except Exception as e:
        print(f"❌ Search error: {e}")
        return json.dumps({"error": str(e)})


# Tool definitions for GPT - UPDATED for v0.7.8
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_lastz_knowledge",
            "description": "Search Last Z game knowledge using semantic vector embeddings. Returns comprehensive game data for text-based queries.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_lastz_screenshot",
            "description": "Analyze LastZ game screenshots for strategic advice. Use when users upload images. Identifies game elements and provides contextual recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_description": {
                        "type": "string",
                        "description": "Poe's automatic image analysis description"
                    },
                    "user_query": {
                        "type": "string",
                        "description": "User's question about the uploaded image"
                    }
                },
                "required": ["image_description", "user_query"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

# Tool definitions properly configured for fastapi-poe compatibility
tool_definitions_fp = [fp.ToolDefinition(
    **tool_dict) for tool_dict in tool_definitions]
tool_executables = [search_lastz_knowledge, analyze_lastz_screenshot]


class LastZImageBot(fp.PoeBot):
    def sanitize_text(self, text):
        """Basic text sanitization for GPT compatibility"""
        if not text:
            return text
        # Replace most common problematic characters
        replacements = {
            "'": "'", """: '"', """: '"',
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
    ):
        """Enhanced response with image + text analysis"""

        # Check for image attachments
        has_images = False
        image_content = ""

        for msg in request.query:
            if msg.attachments:
                has_images = True
                for attachment in msg.attachments:
                    if attachment.parsed_content:
                        image_content += f"\nImage Analysis: {attachment.parsed_content}"
                        print("🖼️ Found image attachment with parsed content")

        # Sanitize the user message
        if request.query:
            sanitized_query = []
            for msg in request.query:
                sanitized_content = self.sanitize_text(msg.content)
                sanitized_query.append(fp.ProtocolMessage(
                    role=msg.role,
                    content=sanitized_content,
                    attachments=msg.attachments  # Preserve attachments
                ))

            # Add enhanced system message for all queries
            system_message = fp.ProtocolMessage(
                role="system",
                content=SYSTEM_PROMPT
            )

            # Insert system message at the beginning
            sanitized_query.insert(0, system_message)

            print(
                f"🔧 Processing query with {len(sanitized_query)} messages, has_images: {has_images}")
            print(
                f"🔧 Available tools: {[tool.__name__ for tool in tool_executables]}")

            # Configure temperature for consistent structured responses
            # 0.0 = fully deterministic for testing/dev phase
            sanitized_request = fp.QueryRequest(
                version=request.version,
                type=request.type,
                query=sanitized_query,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                message_id=request.message_id,
                access_key=request.access_key,
                temperature=0.0  # Deterministic responses for testing consistency
            )
        else:
            sanitized_request = request

        # Stream with enhanced tool calling (image + vector search)
        tool_calls_made = []
        response_chunks = []

        async for msg in fp.stream_request(  # type: ignore
            sanitized_request,
            "GPT-5",
            request.access_key,
            tools=tool_definitions_fp,
            tool_executables=tool_executables,
        ):
            # Track tool calls for debugging
            if hasattr(msg, 'is_suggested_reply') and not msg.is_suggested_reply:
                if hasattr(msg, 'text') and msg.text:
                    response_chunks.append(msg.text)

            # Check for tool call completions (they show up in logs but not easily accessible)
            # We'll add debug footer at the end
            yield msg

        # Add debug footer if we have response content
        if response_chunks:
            debug_info = []
            if debug_tracker["tools_called"]:
                tools_called = ", ".join(debug_tracker["tools_called"])
                debug_info.append(f"🔧 Tools called: {tools_called}")
                debug_info.append(
                    f"📊 Results: {debug_tracker['results_returned']}")
            else:
                debug_info.append(
                    "🚨 NO TOOLS CALLED - POTENTIAL HALLUCINATION")

            debug_info.append(f"🖼️ Has images: {has_images}")

            debug_footer = f"\n\n---\n*Debug: {' | '.join(debug_info)}*"

            # Reset debug tracker for next request
            debug_tracker["tools_called"] = []
            debug_tracker["results_returned"] = 0
            debug_tracker["last_query"] = ""

            yield fp.PartialResponse(
                text=debug_footer,
                is_suggested_reply=False,
                is_replace_response=False
            )

    async def get_settings(self, setting):
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            allow_attachments=True,           # ✅ NEW: Enable image uploads
            enable_image_comprehension=True,  # ✅ NEW: Auto image analysis
            introduction_message=f"Hey there, survivor. How can I help you power up in Last Z: Survival Shooter? Ask me anything. First off, what is your gamertag and headquarters level?\n\n---\n*Last Z Assistant v0.7.8 ({deploy_time}-{deploy_hash[:4]})*"
        )


# Modal setup with image analysis - OPTIMIZED FOR PERFORMANCE
REQUIREMENTS = ["fastapi-poe", "numpy",
                "scikit-learn", "sentence-transformers", "torch"]
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env({"POE_ACCESS_KEY": bot_access_key, "POE_BOT_NAME": bot_name})
    .add_local_dir(
        "/workspaces/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
)
app = App(f"poe-lastz-v0-7-8-{deploy_hash}")


@app.function(
    image=image,
    cpu=4.0,  # 4 vCPUs for image + vector processing
    memory=8192,  # 8GB RAM for embeddings + image analysis
    min_containers=1,  # Keep 1 instance warm to avoid cold starts
    timeout=300,  # 5 minute timeout for image analysis
    scaledown_window=600  # Keep container alive 10 minutes
)
@asgi_app()
def fastapi_app():
    bot = LastZImageBot()
    return fp.make_app(
        bot,
        access_key=bot_access_key,
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name),
    )


if __name__ == "__main__":
    print("🧪 Testing image analysis + vector embeddings...")
    try:
        search = LastZVectorSearch()
        test_result = search.vector_search("best tank hero for early game")
        print(f"✅ Vector test result: Found {len(test_result)} items")

        # Test image analysis
        test_image_desc = "A screenshot showing buildings and heroes in a strategy game interface with upgrade buttons"
        test_image_result = analyze_lastz_screenshot(
            test_image_desc, "what should I upgrade?")
        print(
            f"✅ Image analysis test: {len(test_image_result)} characters response")
    except Exception as e:
        print(f"❌ Test failed: {e}")
