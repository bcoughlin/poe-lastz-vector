#!/usr/bin/env python3
"""
Last Z Bot v0.8.1 - Data Collection with Render Hosting
Migrated from Modal to Render for cost optimization and predictable billing
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

print(f"🚀 Last Z Bot v0.8.1 Render - {deploy_time}")
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
            "bot_version": "0.8.1-render",
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

# Simple knowledge base for POC (in production, load from external source)
knowledge_items = [
    {
        "title": "Hero Recruitment",
        "content": "Focus on recruiting Sophia (tank), Katrina (damage), and Evelyn (support) early game. These heroes form a solid foundation for your team."
    },
    {
        "title": "Headquarters Progression", 
        "content": "Upgrade your headquarters to unlock new buildings and research. Prioritize reaching HQ level 10 for advanced military structures."
    },
    {
        "title": "Research Priorities",
        "content": "Focus on military research first: Infantry Attack, Infantry Defense, then economic research like Construction Speed and Resource Production."
    },
    {
        "title": "Building Placement",
        "content": "Place defensive buildings near your headquarters. Keep resource buildings protected inside your walls. Upgrade walls regularly."
    }
]

knowledge_embeddings = None  # Will store precomputed embeddings

def initialize_knowledge_base():
    """Initialize knowledge base with precomputed OpenAI embeddings"""
    global knowledge_embeddings
    print("🧠 Knowledge base ready (using OpenAI embeddings)")
    print(f"✅ Loaded {len(knowledge_items)} knowledge items")
    # Note: In production, precompute embeddings and store them
    # For POC, we'll compute on-demand to save startup time

# Initialize at startup
initialize_knowledge_base()

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

def search_lastz_knowledge(user_query):
    """Search using OpenAI embeddings"""
    start_time = time.time()
    
    try:
        print(f"🔧 OpenAI embedding search called: '{user_query}'")
        
        # Get embedding for user query
        query_embedding = get_openai_embedding(user_query)
        if not query_embedding:
            return {
                "query": user_query,
                "error": "Failed to get embedding for query",
                "results": []
            }
        
        results = []
        
        # Calculate similarity with each knowledge item
        for item in knowledge_items:
            # Get embedding for knowledge item content
            item_embedding = get_openai_embedding(item["content"])
            if not item_embedding:
                continue
                
            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, item_embedding)
            
            if similarity > 0.2:  # Similarity threshold
                results.append({
                    "content": item["content"],
                    "title": item["title"],
                    "similarity": similarity
                })
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:3]
        
        search_time = time.time() - start_time
        print(f"⚡ OpenAI embedding search: {len(results)} results in {search_time:.2f}s")
        
        return {
            "query": user_query,
            "results": results,
            "total_found": len(results),
            "search_time": search_time
        }
        
    except Exception as e:
        print(f"❌ Search error: {e}")
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
        
        # Simple knowledge search if query contains keywords
        search_result = None
        if any(keyword in user_message.lower() for keyword in ['hero', 'build', 'upgrade', 'strategy', 'research', 'headquarters']):
            tool_calls_made.append('search_lastz_knowledge')
            search_result = search_lastz_knowledge(user_message)
        
        # Create conversation for GPT
        conversation = [
            fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT),
        ]
        
        # Add search results if available
        if search_result and search_result.get('results'):
            knowledge_context = "Based on my Last Z knowledge base:\n\n"
            for result in search_result['results'][:2]:  # Limit to top 2 results
                knowledge_context += f"• {result['title']}: {result['content']}\n"
            
            conversation.append(
                fp.ProtocolMessage(role="system", content=knowledge_context)
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
            "GPT-4",  # Use GPT-4 for Render (GPT-5 might not be available)
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
            server_bot_dependencies={"GPT-4": 1},  # Using GPT-4 for Render compatibility
            allow_attachments=True,           # ✅ Enable image uploads
            enable_image_comprehension=True,  # ✅ Auto image analysis
            introduction_message=f"🎮 Last Z Bot v0.8.1 (Render Hosted)! 🧪 Data collection POC with OpenAI embeddings search. Ask me anything about Last Z strategy! 🧟‍♂️💥\n\nDeployed: {deploy_time} | Hash: {deploy_hash[:4]}"
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
    
    app = fp.make_app(
        bot, 
        access_key=bot_access_key, 
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name)  # Allow fallback during development
    )
    
    return app

# Create the FastAPI app instance
app = create_app()

# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.8.1",
        "hosting": "render",
        "timestamp": datetime.now().isoformat(),
        "deploy_hash": deploy_hash
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)