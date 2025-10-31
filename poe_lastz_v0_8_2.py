#!/usr/bin/env python3
"""
Last Z Bot v0.8.2 - Enhanced Knowledge Delivery with Full JSON Data
- Sends complete structured data (stats, progression, costs) to LLM
- Better handling of hero/building/research queries with precise info
- Maintains disk-based embedding cache for performance
"""

import asyncio
import json
import os
import time
import hashlib
import requests
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional
import tempfile
import logging

import fastapi_poe as fp
from fastapi import FastAPI
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%Y-%m-%d %H:%M")

print(f"🚀 Last Z Bot v0.8.2 Render - {deploy_time}")
print(f"🔑 Deploy hash: {deploy_hash}")

# Data storage configuration for Render
DATA_STORAGE_PATH = os.environ.get("DATA_STORAGE_PATH", "/tmp/lastz_data")
INTERACTIONS_PATH = os.path.join(DATA_STORAGE_PATH, "interactions")
IMAGES_PATH = os.path.join(DATA_STORAGE_PATH, "images")

# Ensure storage directories exist
os.makedirs(INTERACTIONS_PATH, exist_ok=True)
os.makedirs(IMAGES_PATH, exist_ok=True)

# Data collection schema for POC
def create_interaction_log(
    user_id: str,
    conversation_id: str,
    message_id: str,
    user_message: str,
    bot_response: str,
    has_images: bool = False,
    image_count: int = 0,
    image_data: List[Dict[str, Any]] = None,
    tool_calls: List[str] = None,
    response_time: float = 0.0
) -> Dict[str, Any]:
    """Create a structured log entry for user interactions"""
    return {
        "timestamp": datetime.now().isoformat(),
        "session_info": {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "message_id": message_id
        },
        "interaction": {
            "user_message": user_message,
            "user_message_length": len(user_message),
            "has_images": has_images,
            "image_count": image_count,
            "image_data": image_data or [],
            "bot_response": bot_response,
            "bot_response_length": len(bot_response),
            "response_time_ms": round(response_time * 1000, 2)
        },
        "metadata": {
            "tool_calls": tool_calls or [],
            "bot_version": "0.8.2-render-enhanced",
            "deploy_hash": deploy_hash,
            "hosting": "render"
        }
    }

def log_interaction_to_console(interaction_data: Dict[str, Any]):
    """Log interaction data to console for POC testing"""
    print("\n" + "="*80)
    print("📊 DATA COLLECTION POC - INTERACTION LOGGED (RENDER)")
    print("="*80)
    print(f"🕐 Timestamp: {interaction_data['timestamp']}")
    print(f"👤 User ID: {interaction_data['session_info']['user_id']}")
    print(f"💬 Message: {interaction_data['interaction']['user_message'][:100]}...")
    print(f"🖼️  Images: {interaction_data['interaction']['image_count']}")
    if interaction_data['interaction']['image_data']:
        for i, img in enumerate(interaction_data['interaction']['image_data']):
            print(f"   Image {i+1}: {img.get('content_type', 'unknown')} - {img.get('name', 'unnamed')}")
    print(f"🔧 Tools: {', '.join(interaction_data['metadata']['tool_calls'])}")
    print(f"⏱️  Response Time: {interaction_data['interaction']['response_time_ms']}ms")
    print(f"📝 Response Length: {interaction_data['interaction']['bot_response_length']} chars")
    print(f"🏠 Hosting: {interaction_data['metadata']['hosting']}")
    print("="*80)

def store_interaction_data(interaction_data: Dict[str, Any]) -> bool:
    """Store interaction data to local filesystem (Render compatible)"""
    try:
        # Create filename with timestamp and message ID
        timestamp = interaction_data['timestamp'].replace(':', '-').replace('.', '-')
        message_id = interaction_data['session_info']['message_id']
        filename = f"interaction_{timestamp}_{message_id}.json"
        
        # Write interaction data
        filepath = os.path.join(INTERACTIONS_PATH, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(interaction_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Stored interaction data: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to store interaction data: {e}")
        return False

def download_and_store_image(image_url: str, image_name: str, user_id: str, message_id: str) -> Optional[str]:
    """Download image from URL and store to local filesystem (Render compatible)"""
    try:
        print(f"📥 Attempting to download image: {image_url}")
        
        # Make request to download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Create safe filename
        safe_name = "".join(c for c in image_name if c.isalnum() or c in ('_', '-', '.'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{message_id}_{timestamp}_{safe_name}"
        
        # Write image data
        filepath = os.path.join(IMAGES_PATH, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded and stored image: {filepath} ({len(response.content)} bytes)")
        return filepath
        
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return None

# Load system prompt
def load_system_prompt() -> str:
    """Load system prompt with fallback for Render deployment"""
    try:
        # Try loading from local file first
        prompt_paths = [
            "prompts/bot_prompt_v2.md",
            "/app/prompts/bot_prompt_v2.md",
            "./bot_prompt_v2.md"
        ]
        
        for path in prompt_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✅ Loaded prompt from: {path}")
                    return content.strip()
            except FileNotFoundError:
                continue
        
        # Fallback prompt
        print("⚠️  Using fallback system prompt")
        return """You are an enthusiastic Last Z strategy expert who loves helping players optimize their gameplay! 

You have deep knowledge of:
- Hero recruitment, upgrades, and team compositions
- Building placement and headquarters progression  
- Research priorities and tech trees
- Combat strategies and troop management
- Resource optimization and event strategies

Keep your responses conversational, helpful, and strategic. Share specific advice with enthusiasm while being accurate about game mechanics. When you don't know something specific, say so rather than guessing.

CRITICAL: Only reference real hero names like Sophia, Katrina, Evelyn, Marcus, etc. Never make up hero names that don't exist in the game."""
        
    except Exception as e:
        print(f"❌ Error loading prompt: {e}")
        return "You are a Last Z strategy expert. Help players with accurate, enthusiastic advice!"

# Load system prompt at startup
SYSTEM_PROMPT = load_system_prompt()

# Initialize OpenAI client for embeddings
openai_api_key = os.environ.get("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required but not found!")

try:
    print("🤖 Using OpenAI embeddings API (memory-efficient)")
    openai_client = openai.OpenAI(api_key=openai_api_key)
    model = "openai_embeddings"  # Flag for search function
    print(f"✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"❌ OpenAI client initialization failed: {e}")
    raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

# Knowledge base loaded from data files
knowledge_items = []

# Cache for pre-computed embeddings (populated at startup)
knowledge_embeddings = {}

def load_knowledge_base():
    """Load comprehensive knowledge base from data directory (Render compatible)"""
    global knowledge_items
    knowledge_items = []
    
    # Track statistics for debugging
    stats = {
        'json_attempted': 0,
        'json_loaded': 0,
        'json_skipped': 0,
        'md_attempted': 0,
        'md_loaded': 0,
        'md_skipped': 0,
        'errors': []
    }
    
    # Determine data path - try multiple locations for Render compatibility
    data_path_options = [
        "/mnt/data/lastz-rag/data",  # Render Disk mount point (PRODUCTION)
        "../lastz-rag/data",  # Relative path if deployed with repo
        "/app/lastz-rag/data",  # Absolute path on Render (legacy)
        "./data",  # Local development
        os.path.join(os.path.dirname(__file__), "..", "lastz-rag", "data")  # Relative from script location
    ]
    
    data_path = None
    for path in data_path_options:
        if os.path.exists(path):
            data_path = path
            print(f"✅ Found data directory: {path}")
            break
    
    if not data_path:
        print("❌ FATAL ERROR: Data directory not found!")
        print("❌ Searched paths:")
        for path in data_path_options:
            print(f"   - {path}")
        print("❌ Deployment failed - knowledge base required for operation")
        raise RuntimeError("Knowledge base data directory not found. Cannot start bot without data.")
    
    print(f"📚 Loading knowledge base from: {data_path}")
    
    # Load data_index.md configuration
    data_index_path = os.path.join(data_path, "data_index.md")
    if os.path.exists(data_index_path):
        _load_from_data_index(data_path, data_index_path, stats)
    else:
        print("⚠️ data_index.md not found, using legacy loading")
        _load_legacy_hardcoded(data_path, stats)
    
    # Print detailed statistics
    print(f"\n{'='*60}")
    print(f"📊 KNOWLEDGE BASE LOADING SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Total items loaded: {len(knowledge_items)}")
    print(f"\n📄 JSON Files:")
    print(f"   Attempted: {stats['json_attempted']}")
    print(f"   Loaded: {stats['json_loaded']}")
    print(f"   Skipped: {stats['json_skipped']}")
    print(f"\n📝 Markdown Files:")
    print(f"   Attempted: {stats['md_attempted']}")
    print(f"   Loaded: {stats['md_loaded']}")
    print(f"   Skipped: {stats['md_skipped']}")
    if stats['errors']:
        print(f"\n❌ Errors ({len(stats['errors'])}):")
        for error in stats['errors'][:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(stats['errors']) > 10:
            print(f"   ... and {len(stats['errors']) - 10} more errors")
    print(f"{'='*60}\n")

def _parse_data_index(data_index_path):
    """Parse data_index.md to get loading configuration"""
    try:
        with open(data_index_path, encoding='utf-8') as f:
            content = f.read()
        
        config = {
            'core_static': [],
            'dynamic_json_dirs': [],
            'dynamic_json_files': [],
            'dynamic_markdown_dirs': []
        }
        
        # Simple parsing of YAML-like structure in markdown
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            if 'core_static:' in line:
                current_section = 'core_static'
            elif 'directories:' in line and current_section != 'core_static':
                current_section = 'dynamic_json_dirs'
            elif 'files:' in line and current_section != 'core_static':
                current_section = 'dynamic_json_files'
            elif 'dynamic_markdown:' in line:
                current_section = 'dynamic_markdown'
            elif '- file:' in line and current_section == 'core_static':
                # Extract file path
                parts = line.split('"')
                if len(parts) >= 2:
                    config['core_static'].append(parts[1])
            elif '- path:' in line and current_section == 'dynamic_json_dirs':
                # Extract directory path
                parts = line.split('"')
                if len(parts) >= 2:
                    config['dynamic_json_dirs'].append(parts[1].rstrip('/'))
            elif '- path:' in line and current_section == 'dynamic_json_files':
                # Extract file path
                parts = line.split('"')
                if len(parts) >= 2:
                    config['dynamic_json_files'].append(parts[1])
            elif '- path:' in line and current_section == 'dynamic_markdown':
                # Extract directory path
                parts = line.split('"')
                if len(parts) >= 2:
                    config['dynamic_markdown_dirs'].append(parts[1].rstrip('/'))
        
        return config
    except Exception as e:
        print(f"❌ Error parsing data_index.md: {e}")
        return None

def _load_from_data_index(data_path, data_index_path, stats):
    """Load data based on data_index.md configuration"""
    config = _parse_data_index(data_index_path)
    if not config:
        print("⚠️ Failed to parse data_index.md, falling back to legacy loading")
        _load_legacy_hardcoded(data_path, stats)
        return
    
    print(f"📋 Parsed data_index.md configuration")
    
    # Load core static markdown files
    for file_path in config['core_static']:
        full_path = os.path.join(data_path, file_path)
        stats['md_attempted'] += 1
        if os.path.exists(full_path):
            try:
                with open(full_path, encoding='utf-8') as f:
                    content = f.read()
                
                filename = os.path.basename(file_path)
                searchable_text = f"Core Guide: {filename.replace('.md', '').replace('_', ' ').title()} "
                searchable_text += f"Content: {content[:500]}..."
                
                knowledge_items.append({
                    'type': 'core_guide',
                    'name': filename.replace('.md', '').replace('_', ' ').title(),
                    'text': searchable_text,
                    'data': {'filename': filename, 'content': content}
                })
                stats['md_loaded'] += 1
                print(f"✅ Loaded core guide: {filename}")
            except Exception as e:
                stats['md_skipped'] += 1
                stats['errors'].append(f"core/{filename}: {str(e)}")
                print(f"❌ Error loading {file_path}: {e}")
        else:
            stats['md_skipped'] += 1
            stats['errors'].append(f"core/{file_path}: File not found")
    
    # Load JSON directories
    for dir_name in config['dynamic_json_dirs']:
        dir_path = os.path.join(data_path, dir_name)
        print(f"🔍 Looking for JSON directory: {dir_path}")
        if os.path.exists(dir_path):
            print(f"✅ Found directory: {dir_name}, loading...")
            _load_json_directory(dir_path, dir_name, stats)
        else:
            print(f"⚠️ Directory not found: {dir_path}")
            stats['errors'].append(f"JSON directory '{dir_name}' not found at {dir_path}")
    
    # Load individual JSON files
    for file_path in config['dynamic_json_files']:
        full_path = os.path.join(data_path, file_path)
        stats['json_attempted'] += 1
        if os.path.exists(full_path):
            try:
                with open(full_path, encoding='utf-8') as f:
                    data = json.load(f)
                
                filename = os.path.basename(file_path)
                _process_json_file(filename, data)
                stats['json_loaded'] += 1
                print(f"✅ Loaded JSON file: {filename}")
            except Exception as e:
                stats['json_skipped'] += 1
                stats['errors'].append(f"{file_path}: {str(e)}")
                print(f"❌ Error loading {file_path}: {e}")
        else:
            stats['json_skipped'] += 1
            stats['errors'].append(f"{file_path}: File not found")
    
    # Load markdown directories
    for dir_name in config['dynamic_markdown_dirs']:
        # Check both relative to data_path and absolute
        possible_paths = [
            os.path.join(data_path, dir_name),
            os.path.join(data_path, "..", dir_name),  # For directories at repo root
            os.path.join(os.path.dirname(data_path), dir_name)
        ]
        
        found = False
        for dir_path in possible_paths:
            if os.path.exists(dir_path):
                print(f"✅ Found markdown directory: {dir_name} at {dir_path}")
                _load_markdown_directory(dir_path, dir_name, stats)
                found = True
                break
        
        if not found:
            print(f"⚠️ Markdown directory not found: {dir_name}")
            stats['errors'].append(f"Markdown directory '{dir_name}' not found in any search path")

def _load_json_directory(dir_path, dir_name, stats):
    """Load all JSON files from a directory"""
    try:
        for filename in os.listdir(dir_path):
            if filename.endswith('.json'):
                stats['json_attempted'] += 1
                try:
                    with open(os.path.join(dir_path, filename), encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process based on directory type
                    if dir_name == 'heroes':
                        _process_hero_file(filename, data)
                    elif dir_name == 'research':
                        _process_research_file(filename, data)
                    else:
                        _process_generic_json(filename, data, dir_name)
                    stats['json_loaded'] += 1
                except Exception as e:
                    stats['json_skipped'] += 1
                    stats['errors'].append(f"{dir_name}/{filename}: {str(e)}")
                    print(f"❌ Error loading {dir_name}/{filename}: {e}")
    except Exception as e:
        stats['errors'].append(f"Reading directory {dir_path}: {str(e)}")
        print(f"❌ Error reading directory {dir_path}: {e}")

def _load_markdown_directory(dir_path, dir_name, stats):
    """Load all markdown files from a directory"""
    try:
        for filename in os.listdir(dir_path):
            if filename.endswith('.md'):
                stats['md_attempted'] += 1
                try:
                    with open(os.path.join(dir_path, filename), encoding='utf-8') as f:
                        content = f.read()
                    
                    searchable_text = f"{dir_name.upper()} Article: {filename.replace('.md', '').replace('_', ' ').title()} "
                    searchable_text += f"Content: {content[:500]}..."
                    
                    knowledge_items.append({
                        'type': f'{dir_name}_article',
                        'name': filename.replace('.md', '').replace('_', ' ').title(),
                        'text': searchable_text,
                        'data': {'filename': filename, 'content': content, 'directory': dir_name}
                    })
                    stats['md_loaded'] += 1
                    print(f"✅ Loaded {dir_name} article: {filename}")
                except Exception as e:
                    stats['md_skipped'] += 1
                    stats['errors'].append(f"{dir_name}/{filename}: {str(e)}")
                    print(f"❌ Error loading {dir_name}/{filename}: {e}")
    except Exception as e:
        stats['errors'].append(f"Reading directory {dir_path}: {str(e)}")
        print(f"❌ Error reading directory {dir_path}: {e}")

def _process_hero_file(filename, hero_data):
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
    
    knowledge_items.append({
        'type': 'hero',
        'name': hero_data.get('name', filename),
        'text': hero_text,
        'data': hero_data
    })

def _process_research_file(filename, research_data):
    """Process research JSON files"""
    research_text = f"Research: {research_data.get('name', filename)} "
    research_text += f"Category: {research_data.get('category', 'Unknown')} "
    research_text += f"Description: {research_data.get('description', '')}"
    
    knowledge_items.append({
        'type': 'research',
        'name': research_data.get('name', filename),
        'text': research_text,
        'data': research_data
    })

def _process_generic_json(filename, data, directory):
    """Process generic JSON files from directories"""
    content_text = f"{directory.title()} Data: {filename} "
    content_text += f"File containing {len(str(data))} characters of {directory} information"
    
    knowledge_items.append({
        'type': directory,
        'name': filename.replace('.json', '').replace('_', ' ').title(),
        'text': content_text,
        'data': data
    })

def _process_json_file(filename, data):
    """Process different types of JSON files"""
    if filename == 'buildings.json' and 'buildings' in data:
        for building in data['buildings']:
            building_text = f"Building: {building.get('name', 'Unknown')} "
            building_text += f"Type: {building.get('type', 'Unknown')} "
            building_text += f"Function: {building.get('function', '')} "
            if 'produces' in building:
                building_text += f"Produces: {building['produces']} "
            building_text += f"Notes: {building.get('notes', '')}"
            
            knowledge_items.append({
                'type': 'building',
                'name': building.get('name', 'Unknown'),
                'text': building_text,
                'data': building
            })
    elif filename == 'equipment.json':
        # Handle equipment data
        equipment_items = []
        if isinstance(data, list):
            equipment_items = data
        elif 'equipment' in data:
            equipment_items = data['equipment']
        
        for item in equipment_items[:20]:  # Limit to avoid overwhelming
            if isinstance(item, dict):
                item_text = f"Equipment: {item.get('name', 'Unknown')} "
                item_text += f"Type: {item.get('type', 'Unknown')} "
                item_text += f"Stats: {item.get('stats', '')} "
                
                knowledge_items.append({
                    'type': 'equipment',
                    'name': item.get('name', 'Unknown'),
                    'text': item_text,
                    'data': item
                })
    else:
        # Generic JSON file processing
        content_text = f"Data from {filename}: "
        if isinstance(data, dict):
            content_text += f"Contains keys: {', '.join(list(data.keys())[:10])}"
        elif isinstance(data, list):
            content_text += f"Contains {len(data)} items"
        
        knowledge_items.append({
            'type': 'data_file',
            'name': filename.replace('.json', '').replace('_', ' ').title(),
            'text': content_text,
            'data': data
        })

def _load_legacy_hardcoded(data_path, stats):
    """Fallback to hardcoded loading if data_index.md fails"""
    print("🔄 Using legacy hardcoded data loading...")
    
    # Legacy core files
    core_files = ["game_fundamentals.md", "terminology.md", "what_is_lastz.md", "README.md"]
    core_path = os.path.join(data_path, "core")
    
    if os.path.exists(core_path):
        for filename in core_files:
            filepath = os.path.join(core_path, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, encoding='utf-8') as f:
                        content = f.read()
                    
                    searchable_text = f"Core Guide: {filename.replace('.md', '').replace('_', ' ').title()} "
                    searchable_text += f"Content: {content[:500]}..."
                    
                    knowledge_items.append({
                        'type': 'core_guide',
                        'name': filename.replace('.md', '').replace('_', ' ').title(),
                        'text': searchable_text,
                        'data': {'filename': filename, 'content': content}
                    })
                    print(f"✅ Loaded legacy core guide: {filename}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")
    
    # Legacy directory scans
    for directory in ['heroes', 'research']:
        dir_path = os.path.join(data_path, directory)
        if os.path.exists(dir_path):
            _load_json_directory(dir_path, directory)

# Note: Knowledge base is loaded in app startup event (after disk is mounted)
# See @app.on_event("startup") below

def cosine_similarity(a, b):
    """Simple cosine similarity calculation"""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0
    return dot_product / (magnitude_a * magnitude_b)

def get_openai_embedding(text: str) -> List[float]:
    """Get embedding from OpenAI API"""
    try:
        if not openai_client:
            print("❌ OpenAI client not available")
            return []
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",  # Cost-effective model
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ OpenAI embedding error: {e}")
        return []

def get_embeddings_cache_path():
    """Get the path to the embeddings cache file on Render Disk"""
    # Try Render Disk first, fall back to temp for local dev
    cache_locations = [
        "/mnt/data/lastz-rag/embeddings_cache.json",  # Render Disk (persistent)
        "/tmp/embeddings_cache.json"  # Fallback for local dev
    ]
    
    for path in cache_locations:
        dir_path = os.path.dirname(path)
        if os.path.exists(dir_path) and os.access(dir_path, os.W_OK):
            return path
    
    # Last resort - current directory
    return "embeddings_cache.json"

def calculate_knowledge_hash():
    """Calculate hash of knowledge base to detect changes"""
    # Create a deterministic string from all knowledge items
    content = ""
    for item in sorted(knowledge_items, key=lambda x: x.get('name', '')):
        content += f"{item.get('type', '')}:{item.get('name', '')}:{item.get('text', '')[:100]}"
    
    return hashlib.md5(content.encode()).hexdigest()

def load_embeddings_from_disk():
    """Load cached embeddings from disk if available and valid"""
    global knowledge_embeddings
    
    cache_path = get_embeddings_cache_path()
    
    if not os.path.exists(cache_path):
        print(f"📂 No embeddings cache found at {cache_path}")
        return False
    
    try:
        print(f"📂 Loading embeddings cache from {cache_path}")
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        # Verify cache is valid for current knowledge base
        cached_hash = cache_data.get('knowledge_hash', '')
        current_hash = calculate_knowledge_hash()
        
        if cached_hash != current_hash:
            print(f"⚠️  Cache invalid - knowledge base changed (hash mismatch)")
            print(f"   Cached: {cached_hash[:8]}... Current: {current_hash[:8]}...")
            return False
        
        knowledge_embeddings = cache_data.get('embeddings', {})
        cache_version = cache_data.get('version', 'unknown')
        
        print(f"✅ Loaded {len(knowledge_embeddings)} embeddings from disk cache")
        print(f"   Cache version: {cache_version}, hash: {current_hash[:8]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error loading embeddings cache: {e}")
        return False

def save_embeddings_to_disk():
    """Save embeddings cache to disk for persistence across restarts"""
    cache_path = get_embeddings_cache_path()
    
    try:
        cache_data = {
            'version': '0.8.1',
            'timestamp': datetime.now().isoformat(),
            'knowledge_hash': calculate_knowledge_hash(),
            'embeddings_count': len(knowledge_embeddings),
            'embeddings': knowledge_embeddings
        }
        
        print(f"💾 Saving embeddings cache to {cache_path}")
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
        
        # Get file size for logging
        file_size = os.path.getsize(cache_path) / (1024 * 1024)  # MB
        print(f"✅ Saved {len(knowledge_embeddings)} embeddings to disk ({file_size:.2f} MB)")
        
    except Exception as e:
        print(f"❌ Error saving embeddings cache: {e}")

def precompute_knowledge_embeddings():
    """Pre-compute embeddings for all knowledge items (with disk caching)"""
    global knowledge_embeddings
    
    # Try to load from disk first
    if load_embeddings_from_disk():
        print("🚀 Using cached embeddings from disk - no API calls needed!")
        return
    
    # Cache miss or invalid - generate embeddings
    knowledge_embeddings = {}
    print(f"🔄 Generating embeddings for {len(knowledge_items)} knowledge items...")
    print(f"   (This only happens when knowledge base changes)")
    start_time = time.time()
    
    for idx, item in enumerate(knowledge_items):
        # Get the searchable text from the item
        searchable_text = item.get("text", "")
        if not searchable_text:
            continue
        
        # Generate a unique key for this item
        item_key = f"{item.get('type', 'unknown')}_{item.get('name', 'unnamed')}_{idx}"
        
        # Get embedding for knowledge item
        item_embedding = get_openai_embedding(searchable_text)
        if item_embedding:
            knowledge_embeddings[item_key] = item_embedding
            
        # Progress indicator every 20 items
        if (idx + 1) % 20 == 0:
            print(f"   ⏳ Progress: {idx + 1}/{len(knowledge_items)} items embedded...")
    
    elapsed_time = time.time() - start_time
    print(f"✅ Generated {len(knowledge_embeddings)} embeddings in {elapsed_time:.2f}s")
    print(f"   Average: {elapsed_time/len(knowledge_embeddings):.3f}s per embedding")
    
    # Save to disk for next restart
    save_embeddings_to_disk()


def search_lastz_knowledge(user_query):
    """Search using OpenAI embeddings with comprehensive knowledge base"""
    start_time = time.time()
    
    try:
        print(f"🔧 OpenAI embedding search called: '{user_query}'")
        print(f"📚 Searching {len(knowledge_items)} knowledge items using cached embeddings")
        
        # Get embedding for user query (only 1 API call per query)
        query_embedding = get_openai_embedding(user_query)
        if not query_embedding:
            return {
                "query": user_query,
                "error": "Failed to get embedding for query",
                "results": []
            }
        
        results = []
        
        # Calculate similarity with each knowledge item using cached embeddings
        for idx, item in enumerate(knowledge_items):
            # Generate the same key used during pre-computation
            item_key = f"{item.get('type', 'unknown')}_{item.get('name', 'unnamed')}_{idx}"
            
            # Get pre-computed embedding from cache
            item_embedding = knowledge_embeddings.get(item_key)
            if not item_embedding:
                # Skip items without cached embeddings
                continue
                
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, item_embedding)
            
            if similarity > 0.2:  # Similarity threshold
                # Extract content for display - ENHANCED FOR v0.8.2
                item_type = item.get("type", "unknown")
                item_data = item.get("data", {})
                
                # For structured data types (JSON), send the full data
                if item_type in ['hero', 'research', 'building', 'equipment'] and isinstance(item_data, dict):
                    # Format structured JSON data for LLM consumption
                    content = json.dumps(item_data, indent=2)
                else:
                    # For markdown/text content, use the text or content field
                    searchable_text = item.get("text", "")
                    content = searchable_text
                    if 'content' in item_data:
                        content = item_data['content'][:1000]  # Increased limit for better context
                
                results.append({
                    "content": content,
                    "title": item.get("name", "Unknown"),
                    "type": item_type,
                    "similarity": similarity,
                    "is_structured": item_type in ['hero', 'research', 'building', 'equipment']
                })
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:5]  # Increased from 3 to 5 for better context
        
        search_time = time.time() - start_time
        print(f"⚡ OpenAI embedding search: {len(results)} results in {search_time:.2f}s (using cache)")
        if results:
            print(f"   Top result: {results[0]['title']} (similarity: {results[0]['similarity']:.3f})")
        
        return {
            "query": user_query,
            "results": results,
            "total_found": len(results),
            "search_time": search_time
        }
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "query": user_query,
            "error": str(e),
            "results": []
        }

class LastZBot(fp.PoeBot):
    """Last Z Strategy Bot v0.8.1 - Render Hosted Data Collection POC"""
    
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterator[fp.PartialResponse]:
        start_time = time.time()
        
        # Extract request information for data collection
        user_id = getattr(request, 'user_id', 'unknown')
        conversation_id = getattr(request, 'conversation_id', 'unknown')
        message_id = getattr(request, 'message_id', 'unknown')
        
        # Get user message and check for images
        user_message = ""
        has_images = False
        image_count = 0
        image_data = []
        
        if request.query:
            latest_message = request.query[-1]
            print(f"🔍 Message structure debug:")
            print(f"   - Has content attr: {hasattr(latest_message, 'content')}")
            print(f"   - Content type: {type(getattr(latest_message, 'content', None))}")
            print(f"   - Has attachments attr: {hasattr(latest_message, 'attachments')}")
            
            if hasattr(latest_message, 'content'):
                if isinstance(latest_message.content, str):
                    user_message = latest_message.content
                    print(f"   - String content: {user_message[:100]}...")
                elif isinstance(latest_message.content, list):
                    print(f"   - List content with {len(latest_message.content)} items")
                    # Handle content array (text + images)
                    text_parts = []
                    for i, content_part in enumerate(latest_message.content):
                        print(f"     Content part {i}: {type(content_part)}")
                        if hasattr(content_part, 'type'):
                            print(f"       Type: {content_part.type}")
                            if content_part.type == 'text':
                                text_parts.append(content_part.text)
                                print(f"       Text: {content_part.text}")
                            elif content_part.type == 'image_url':
                                has_images = True
                                image_count += 1
                                print(f"       ✅ IMAGE DETECTED!")
                        else:
                            print(f"       No type attribute: {dir(content_part)}")
                    user_message = " ".join(text_parts)
            
            # Also check for attachments and extract detailed info
            if hasattr(latest_message, 'attachments') and latest_message.attachments:
                print(f"   - Attachments found: {len(latest_message.attachments)}")
                for i, attachment in enumerate(latest_message.attachments):
                    print(f"     Attachment {i}: {type(attachment)}")
                    
                    # Extract attachment data
                    attachment_info = {
                        "index": i,
                        "content_type": getattr(attachment, 'content_type', None),
                        "name": getattr(attachment, 'name', None),
                        "url": getattr(attachment, 'url', None),
                        "size": getattr(attachment, 'size', None),
                        "parsed_content": getattr(attachment, 'parsed_content', None)
                    }
                    
                    # Log all available attributes for debugging
                    print(f"       Content Type: {attachment_info['content_type']}")
                    print(f"       Name: {attachment_info['name']}")
                    print(f"       URL: {attachment_info['url']}")
                    print(f"       Size: {attachment_info['size']}")
                    
                    image_data.append(attachment_info)
                    has_images = True
                    image_count += 1
        
        print(f"🔧 Processing query with {len(request.query)} messages, has_images: {has_images}")
        
        # Track tool calls for data collection
        tool_calls_made = []
        
        # ALWAYS run knowledge search for every query to prevent hallucinations
        search_result = None
        print(f"🔎 Running knowledge base search for: {user_message[:100]}...")
        tool_calls_made.append('search_lastz_knowledge')
        search_result = search_lastz_knowledge(user_message)
        print(f"🔍 Search found {len(search_result.get('results', []))} results")
        
        # Create conversation for GPT
        conversation = [
            fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT),
        ]
        
        # Add search results if available - ENHANCED FOR v0.8.2
        if search_result and search_result.get('results'):
            knowledge_context = "=== KNOWLEDGE BASE SEARCH RESULTS ===\n"
            knowledge_context += "You MUST base your answer ONLY on this information. DO NOT add information from your general knowledge.\n\n"
            
            for idx, result in enumerate(search_result['results'][:3], 1):  # Top 3 results
                knowledge_context += f"{idx}. {result['title']} (type: {result['type']}, relevance: {result['similarity']:.2f})\n"
                
                # For structured data, provide clear formatting
                if result.get('is_structured'):
                    knowledge_context += f"   STRUCTURED DATA (JSON):\n"
                    # Indent the JSON for readability
                    for line in result['content'].split('\n'):
                        knowledge_context += f"   {line}\n"
                else:
                    # For text/markdown content
                    knowledge_context += f"   {result['content'][:500]}...\n"
                
                knowledge_context += "\n"
            
            conversation.append(
                fp.ProtocolMessage(role="system", content=knowledge_context)
            )
        else:
            # NO RESULTS - Add explicit constraint to prevent hallucination
            no_results_warning = """=== NO KNOWLEDGE BASE RESULTS FOUND ===

CRITICAL: The knowledge base search returned no relevant results for this query.

You MUST respond with:
"I don't have specific information about that in my knowledge base. Could you rephrase your question or ask about:
- Hero strategies (Sophia, Katrina, Evelyn, Fiona, etc.)
- Building and HQ upgrades
- Research priorities
- Combat tactics
- Resource management"

DO NOT attempt to answer from general knowledge. DO NOT make up hero names or game features."""
            
            conversation.append(
                fp.ProtocolMessage(role="system", content=no_results_warning)
            )
        
        # Add user messages from request
        for msg in request.query:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                conversation.append(msg)
        
        # Create sanitized request
        sanitized_request = fp.QueryRequest(
            version=request.version,
            type=request.type,
            query=conversation,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            access_key=request.access_key,
        )
        
        # Collect bot response for logging
        bot_response_parts = []
        
        async for msg in fp.stream_request(
            sanitized_request,
            "GPT-5-Chat",  # Use GPT-5-Chat for Poe platform
            request.access_key,
        ):
            if hasattr(msg, 'text') and msg.text:
                bot_response_parts.append(msg.text)
            yield msg
        
        # Calculate response time and create interaction log
        response_time = time.time() - start_time
        bot_response = "".join(bot_response_parts)
        
        # Try to download and store images if URLs are available
        for img_info in image_data:
            if img_info.get('url') and img_info.get('name'):
                try:
                    stored_path = download_and_store_image(
                        img_info['url'], 
                        img_info['name'], 
                        user_id, 
                        message_id
                    )
                    if stored_path:
                        img_info['stored_path'] = stored_path
                except Exception as e:
                    print(f"❌ Error downloading image: {e}")
        
        # Create and log interaction data (POC)
        interaction_data = create_interaction_log(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            user_message=user_message,
            bot_response=bot_response,
            has_images=has_images,
            image_count=image_count,
            image_data=image_data,
            tool_calls=tool_calls_made,
            response_time=response_time
        )
        
        # Log to console for POC testing
        log_interaction_to_console(interaction_data)
        
        # Store interaction data to filesystem
        store_interaction_data(interaction_data)

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5-Chat": 1},  # Using GPT-5-Chat for Poe platform
            allow_attachments=True,           # ✅ Enable image uploads
            enable_image_comprehension=True,  # ✅ Auto image analysis
            introduction_message="🎮 Hey there! I'm your Last Z: Survival Shooter strategy expert! �‍♂️💥\n\nI can help you with:\n• Hero strategies & team builds 🦸‍♀️\n• Base building & upgrades 🏰\n• Research priorities 🔬\n• Combat tactics ⚔️\n• Screenshot analysis �\n\nDrop your questions or share screenshots - let's dominate the apocalypse together! 🔥"
        )

# Create FastAPI app for Render deployment
def create_app():
    """Create FastAPI application for Render hosting"""
    bot = LastZBot()
    
    # Get credentials from environment variables
    bot_access_key = os.environ.get("POE_ACCESS_KEY")
    bot_name = os.environ.get("POE_BOT_NAME")
    
    print(f"🔐 Bot access key: {'✅ Found' if bot_access_key else '❌ Missing'}")
    print(f"🤖 Bot name: {bot_name}")
    print(f"🏠 Hosting: Render")
    
    # Note: Not passing bot_name to fp.make_app to avoid "asyncio.run() cannot be called 
    # from a running event loop" error during startup. Bot settings can be synced manually
    # using the sync_settings.py script if needed. The bot still works without auto-sync.
    app = fp.make_app(
        bot, 
        access_key=bot_access_key,
        allow_without_key=not bot_access_key  # Allow fallback during development
    )
    
    return app

# Create the FastAPI app instance
app = create_app()

@app.on_event("startup")
async def startup_event():
    """Load knowledge base after app starts (when disk is mounted)"""
    print("🚀 App startup - loading knowledge base...")
    load_knowledge_base()
    print(f"✅ Knowledge base loaded - {len(knowledge_items)} items")
    
    # Pre-compute embeddings for all knowledge items (one-time cost at startup)
    print("🔄 Pre-computing embeddings for knowledge base...")
    precompute_knowledge_embeddings()
    print(f"✅ Startup complete - {len(knowledge_items)} items with {len(knowledge_embeddings)} cached embeddings")

# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.8.2",
        "hosting": "render",
        "timestamp": datetime.now().isoformat(),
        "deploy_hash": deploy_hash,
        "knowledge_items": len(knowledge_items),
        "cached_embeddings": len(knowledge_embeddings),
        "enhancements": "Full JSON data delivery for structured content"
    }

@app.post("/admin/refresh-data")
async def refresh_data(api_key: str):
    """Admin endpoint to refresh knowledge base without redeploying"""
    import subprocess
    
    # Simple API key check (set ADMIN_API_KEY in Render env vars)
    expected_key = os.environ.get("ADMIN_API_KEY", "")
    if not expected_key or api_key != expected_key:
        return {"error": "Unauthorized"}, 401
    
    try:
        # Run git pull on the mounted data directory
        result = subprocess.run(
            ["git", "-C", "/mnt/data/lastz-rag", "pull", "origin", "main"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Reload knowledge base
            old_count = len(knowledge_items)
            load_knowledge_base()
            new_count = len(knowledge_items)
            
            return {
                "status": "success",
                "git_output": result.stdout,
                "old_count": old_count,
                "new_count": new_count,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "git_error": result.stderr,
                "returncode": result.returncode
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)