"""
Last Z: Survival Shooter Assistant V7.4 - Local Data Mount Architecture  
Pure GPT-5 tool calling with local data mounting for reliable knowledge loading.
No volume complexity - direct local data access.
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
deploy_time = datetime.now().strftime("%H:%M")

# Modal app
app = modal.App(f"poe-lastz-v7-4-{deploy_hash}")

# Create image with dependencies and local data
image = (
    modal.Image.debian_slim()
    .pip_install([
        "fastapi-poe==0.0.48",
        "sentence-transformers",
        "scikit-learn", 
        "numpy",
        "pyyaml"
    ])
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
)

class LastZBotV74:
    def __init__(self):
        self._knowledge_items = []
        self._embeddings = None
        self._encoder = None
        
    def sanitize_text(self, text):
        """Clean text to prevent unicode encoding errors with GPT models"""
        if not text:
            return text
            
        # Replace problematic unicode characters
        replacements = {
            "'": "'",       # Right single quotation mark
            "'": "'",       # Left single quotation mark  
            """: '"',       # Left double quotation mark
            """: '"',       # Right double quotation mark
            "–": "--",      # En dash
            "—": "--",      # Em dash
            "…": "...",     # Horizontal ellipsis
            "•": "*",       # Bullet point
            "®": "(R)",     # Registered trademark
            "™": "(TM)",    # Trademark
            "©": "(C)",     # Copyright
            "§": "Section", # Section sign
            "¶": "Para",    # Pilcrow (paragraph)
            "†": "+",       # Dagger
            "‡": "++",      # Double dagger
            "°": " degrees", # Degree symbol
            "µ": "micro",   # Micro sign
            "€": "EUR",     # Euro sign
            "£": "GBP",     # Pound sign
            "¥": "JPY",     # Yen sign
            "¢": "cents",   # Cent sign
            "α": "alpha",   # Greek alpha
            "β": "beta",    # Greek beta
            "γ": "gamma",   # Greek gamma
            "δ": "delta",   # Greek delta
            "π": "pi",      # Greek pi
            "Ω": "Omega",   # Greek omega
            "∞": "infinity", # Infinity
            "≠": "!=",      # Not equal
            "≤": "<=",      # Less than or equal
            "≥": ">=",      # Greater than or equal
            "±": "+/-",     # Plus-minus
            "×": "x",       # Multiplication sign
            "÷": "/",       # Division sign
            "√": "sqrt",    # Square root
            "∑": "sum",     # Summation
            "∆": "delta",   # Delta (increment)
            "∫": "integral", # Integral
        }
        
        for unicode_char, replacement in replacements.items():
            text = text.replace(unicode_char, replacement)
        
        # Encode to ASCII, replacing any remaining non-ASCII characters
        try:
            text = text.encode('ascii', 'replace').decode('ascii')
        except Exception:
            # Fallback: remove non-ASCII characters entirely
            text = ''.join(char for char in text if ord(char) < 128)
            
        return text

    def _init_vector_search(self):
        """Initialize vector search with sentence transformers"""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._encoder = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Load all knowledge from local mount
                all_knowledge = self.load_all_knowledge()
                texts = [item["text"] for item in all_knowledge]
                
                self._embeddings = self._encoder.encode(texts)
                self._knowledge_items = all_knowledge  # Store full knowledge items
                
                print(f"✅ Vector search ready: {len(texts)} items from local mount")
            except Exception as e:
                self._encoder = "fallback"
                print(f"⚠️ Vector search failed, using keyword search: {e}")
                # Still store the knowledge items for keyword search
                if hasattr(self, '_knowledge_items'):
                    print(f"📝 Knowledge available for keyword search: {len(self._knowledge_items)} items")

    def load_all_knowledge(self):
        """Load all knowledge from local mounted data"""
        knowledge = []
        
        try:
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
            print(f"Local mount loading failed: {e}")
        
        # Return what we actually loaded - no fallbacks for transparent debugging
        if not knowledge:
            print("❌ No knowledge loaded - check local mount")
        else:
            print(f"✅ Loaded {len(knowledge)} knowledge items from local mount")
            
        return knowledge

    def parse_data_index(self, index_path):
        """Parse the data_index.md file to get loading instructions"""
        try:
            with open(index_path, 'r') as f:
                content = f.read()
            
            # Extract YAML blocks and parse them
            yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
            
            parsed_data = {}
            for block in yaml_blocks:
                try:
                    import yaml
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
            
            # Split by headers and process sections
            sections = re.split(r'\n(?=#+\s)', content)
            
            for section in sections:
                if section.strip():
                    lines = section.split('\n')
                    if lines:
                        # Extract header if present
                        header_match = re.match(r'^#+\s+(.+)', lines[0])
                        if header_match:
                            title = header_match.group(1)
                            body = '\n'.join(lines[1:]).strip()
                        else:
                            title = "General Information"
                            body = section.strip()
                        
                        if body:
                            text = f"{title}: {body}"
                            tags = [title.lower()]
                            knowledge.append({"text": text, "tags": tags})
            
            return knowledge
            
        except Exception as e:
            print(f"Failed to parse markdown file {file_path}: {e}")
            return []

    def search_knowledge(self, query, num_results=5):
        """Search knowledge using vector similarity"""
        try:
            self._init_vector_search()
            
            if self._encoder == "fallback" or not self._knowledge_items:
                # Fallback to keyword search
                return self.keyword_search(query, num_results)
            
            # Encode query
            query_embedding = self._encoder.encode([query])
            
            # Calculate similarities
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(query_embedding, self._embeddings)[0]
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:num_results]
            
            results = []
            for idx in top_indices:
                results.append({
                    "text": self._knowledge_items[idx]["text"],
                    "tags": self._knowledge_items[idx]["tags"],
                    "score": float(similarities[idx])
                })
            
            return results
            
        except Exception as e:
            print(f"Vector search failed: {e}")
            return self.keyword_search(query, num_results)

    def keyword_search(self, query, num_results=5):
        """Fallback keyword search"""
        if not self._knowledge_items:
            return []
        
        query_lower = query.lower()
        scored_items = []
        
        for item in self._knowledge_items:
            score = 0
            text_lower = item["text"].lower()
            
            # Score based on query word matches
            for word in query_lower.split():
                if word in text_lower:
                    score += 1
                    
            # Bonus for tag matches
            for tag in item["tags"]:
                if query_lower in tag or tag in query_lower:
                    score += 2
            
            if score > 0:
                scored_items.append((score, item))
        
        # Sort by score and return top results
        scored_items.sort(reverse=True, key=lambda x: x[0])
        return [{"text": item[1]["text"], "tags": item[1]["tags"], "score": item[0]} 
                for item in scored_items[:num_results]]

    def get_knowledge(self, query):
        """Get relevant knowledge for a query"""
        results = self.search_knowledge(query)
        if results:
            knowledge_text = "\n\n".join([f"• {result['text']}" for result in results])
            return f"Relevant knowledge:\n{knowledge_text}"
        return "No relevant knowledge found for this query."

    async def get_response_content(self, query):
        """Process query and return enhanced content"""
        user_message = query.query[-1].content if query.query else ""
        sanitized_message = self.sanitize_text(user_message)
        
        # Detect keywords and get relevant knowledge
        knowledge = ""
        keywords = ["natalie", "hero", "level", "power", "upgrade", "headquarters", "hq", "troops", "research", "equipment"]
        if any(keyword in sanitized_message.lower() for keyword in keywords):
            knowledge = self.get_knowledge(sanitized_message)
        
        # Create enhanced query with context
        enhanced_query = fp.QueryRequest(
            version=query.version,
            type=query.type, 
            query=[
                fp.ProtocolMessage(role="system", content="You are a Last Z strategy expert. Use the provided knowledge to give specific, detailed advice."),
                fp.ProtocolMessage(role="user", content=sanitized_message),
                fp.ProtocolMessage(role="assistant", content=knowledge)
            ],
            user_id=query.user_id,
            conversation_id=query.conversation_id,
            message_id=query.message_id
        )
        
        # Stream from GPT-5 with knowledge context
        async for msg in fp.stream_request(enhanced_query, "GPT-5", query.access_key):
            yield msg

# Create bot instance (moved inside function to avoid global state)

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_dict({
            "POE_ACCESS_KEY": "DjeSMuL0QwiwBSLa33Pa6t97kxhEmmXb",
            "POE_BOT_NAME": "LastZBetaV7",
        })
    ],
)
@modal.asgi_app()
def fastapi_app():
    bot = LastZBotV74()
    return fp.make_app(bot, access_key=os.environ["POE_ACCESS_KEY"], bot_name=os.environ["POE_BOT_NAME"])

# Settings endpoint
@app.function(image=image)
def get_settings():
    """Get bot settings"""
    return fp.SettingsResponse(
        server_bot_dependencies={"GPT-5": 1},
        allow_attachments=True,
        introduction_message=f"Last Z Strategy Assistant V7.4 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🎯 **Expert Last Z guidance with local data mount**\n\nI have access to comprehensive game knowledge including:\n• All hero data with power calculations\n• Headquarters upgrade paths\n• Troop compositions and strategies\n• Research priorities\n• Equipment optimization\n\n**Test baseline**: Ask about Natalie at level 18 (should show ~20500 power)\n\n✨ Ready to help optimize your Last Z strategy!"
    )

if __name__ == "__main__":
    # Test data loading locally
    bot = LastZBotV74()
    knowledge = bot.load_all_knowledge()
    print(f"Local test: Loaded {len(knowledge)} knowledge items")
    if knowledge:
        print("Sample knowledge:", knowledge[0])