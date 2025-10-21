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
            with open(index_path, 'r', encoding='utf-8') as f:
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
            
            print(f"📋 Parsed data_index.md: {len(config['core_static'])} core files, {len(config['dynamic_json_dirs'])} JSON dirs, {len(config['dynamic_json_files'])} JSON files")
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
                    with open(full_path, 'r', encoding='utf-8') as f:
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
                    with open(filepath, 'r') as f:
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
                    with open(f"{dir_path}/{filename}", 'r') as f:
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
                    with open(f"{dir_path}/{filename}", 'r', encoding='utf-8') as f:
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
        core_files = ["game_fundamentals.md", "terminology.md", "what_is_lastz.md", "README.md"]
        core_path = f"{data_path}/core"
        
        if os.path.exists(core_path):
            for filename in core_files:
                filepath = f"{core_path}/{filename}"
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
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
            elif 'equipment' in data:
                equipment_items = data['equipment']
            elif 'items' in data:
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
    
    def vector_search(self, query: str, min_similarity: float = 0.20) -> List[Dict[str, Any]]:
        """True vector search using semantic similarity - optimized for performance"""
        if not self.model or self.embeddings is None:
            print("⚠️ Falling back to keyword search - embeddings not available")
            return self.simple_text_search(query)
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import time
            
            start_time = time.time()
            
            # Create query embedding
            query_embedding = self.model.encode([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, self.embeddings)[0]
            
            # Get all results above threshold, sorted by relevance
            # Use numpy for faster processing
            relevant_indices = np.where(similarities > min_similarity)[0]
            relevant_similarities = similarities[relevant_indices]
            
            # Sort by similarity (descending)
            sorted_indices = relevant_indices[np.argsort(relevant_similarities)[::-1]]
            
            results = []
            for idx in sorted_indices:
                item = self.knowledge_items[idx].copy()
                item['similarity_score'] = float(similarities[idx])
                results.append(item)
            
            search_time = time.time() - start_time
            print(f"⚡ Vector search: {len(results)} results in {search_time:.2f}s (similarity {min_similarity}+)")
            if results:
                print(f"Top similarity: {results[0]['similarity_score']:.3f}, Lowest: {results[-1]['similarity_score']:.3f}")
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
        
        # Perform optimized vector search
        results = vector_search.vector_search(user_query)
        
        # Smart result limiting for performance
        if len(results) > 50:
            print(f"📊 Large result set ({len(results)}), limiting to top 50 for GPT processing")
            results = results[:50]
        
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
        
        # Create debug citations
        citations = []
        for item in results[:10]:  # Top 10 for citations
            score = item.get('similarity_score', item.get('keyword_score', 0))
            citations.append(f"{item['name']} ({item['type']}, {score:.3f})")
        
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

# Tool definitions for GPT
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_lastz_knowledge",
            "description": "Search Last Z game knowledge using semantic vector embeddings. Returns comprehensive game data that GPT will analyze and synthesize into clean, helpful responses. Focus on providing clear, actionable advice without cluttering the response with inline citations. A concise source list will be automatically added at the end for reference.",
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
            
            # Add system message for clean responses with debug citations
            system_message = fp.ProtocolMessage(
                role="system",
                content="You are a Last Z strategy expert. Provide clear, helpful responses without inline citations. When you receive search results with a 'debug_citations' field, include those exact citations at the end of your response for reference. Focus on actionable advice and clear explanations."
            )
            
            # Insert system message at the beginning
            sanitized_query.insert(0, system_message)
            
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
            "GPT-5-mini",
            request.access_key,
            tools=tool_definitions_fp,
            tool_executables=tool_executables,
        ):
            yield msg

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5-mini": 1},
            allow_attachments=False,
            introduction_message=f"Last Z Assistant V7.7 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🧠 TRUE VECTOR EMBEDDINGS with Semantic Search\n\n✅ AI-powered semantic understanding:\n• Heroes (roles, skills, strategies)\n• Buildings (scaling, synergies)\n• Equipment (optimal loadouts)\n\n🔍 Finds conceptually related information, not just keywords!\n🎯 Includes similarity scores for transparency\n⚡ Powered by GPT-5-mini for speed & efficiency!\n\n💡 Try: 'Early game tank strategy' or 'Heroes that synergize with resource buildings'"
        )

# Modal setup with vector embeddings - OPTIMIZED FOR PERFORMANCE
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

@app.function(
    image=image,
    cpu=4.0,  # 4 vCPUs for faster processing
    memory=8192,  # 8GB RAM for large embeddings
    min_containers=1,  # Keep 1 instance warm to avoid cold starts
    timeout=300,  # 5 minute timeout for long queries
    scaledown_window=600  # Keep container alive 10 minutes
)
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