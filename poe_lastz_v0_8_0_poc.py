#!/usr/bin/env python3
"""
Last Z Bot v0.8.0 - Data Collection POC
Testing what user interaction data we can collect via Poe framework
"""

import asyncio
import json
import os
import time
import hashlib
import requests
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional

import modal
import fastapi_poe as fp
from modal import App, Image, asgi_app, Volume
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Bot configuration
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%Y-%m-%d %H:%M")

# Dependencies for Modal - using exact working versions from v0.7.9
REQUIREMENTS = ["fastapi-poe", "numpy", "scikit-learn", "sentence-transformers", "torch", "requests"]

print(f"🚀 Last Z Bot v0.8.0 POC - {deploy_time}")
print(f"🔑 Deploy hash: {deploy_hash}")

# Create Modal Volume for persistent data storage
volume = Volume.from_name("lastz-data-collection", create_if_missing=True)

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
            "bot_version": "0.8.0-poc",
            "deploy_hash": deploy_hash
        }
    }

def log_interaction_to_console(interaction_data: Dict[str, Any]):
    """Log interaction data to console for POC testing"""
    print("\n" + "="*80)
    print("📊 DATA COLLECTION POC - INTERACTION LOGGED")
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
    print("="*80)

def store_interaction_data(interaction_data: Dict[str, Any], volume_path: str = "/app/storage/interactions") -> bool:
    """Store interaction data to Modal Volume"""
    try:
        # Create filename with timestamp and message ID
        timestamp = interaction_data['timestamp'].replace(':', '-').replace('.', '-')
        message_id = interaction_data['session_info']['message_id']
        filename = f"interaction_{timestamp}_{message_id}.json"
        
        # Ensure directory exists
        os.makedirs(volume_path, exist_ok=True)
        
        # Write interaction data
        filepath = os.path.join(volume_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(interaction_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Stored interaction data: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to store interaction data: {e}")
        return False

def download_and_store_image(image_url: str, image_name: str, user_id: str, message_id: str, volume_path: str = "/app/storage/images") -> Optional[str]:
    """Download image from URL and store to Modal Volume"""
    try:
        print(f"📥 Attempting to download image: {image_url}")
        
        # Make request to download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Create safe filename
        safe_name = "".join(c for c in image_name if c.isalnum() or c in ('_', '-', '.'))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_{message_id}_{timestamp}_{safe_name}"
        
        # Ensure directory exists
        os.makedirs(volume_path, exist_ok=True)
        
        # Write image data
        filepath = os.path.join(volume_path, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded and stored image: {filepath} ({len(response.content)} bytes)")
        return filepath
        
    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return None

# Load system prompt from file
def load_prompt_file(filename: str) -> str:
    """Load prompt from mounted files with fallback"""
    try:
        # Mirror the data loading approach - try /app/prompts first (Modal mount)
        paths = [
            f"/app/prompts/{filename}",  # Modal mount path (like /app/data)
            f"/root/prompts/{filename}",  # Alternative Modal path
            f"prompts/{filename}",       # Local development path
        ]
        
        for path in paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"✅ Loaded prompt from: {path}")
                    return content.strip()
            except FileNotFoundError:
                continue
        
        print(f"❌ Prompt file {filename} not found in any expected location")
        print(f"🔍 Tried paths: {paths}")
        return "You are a Last Z strategy expert. Help players optimize their gameplay with enthusiasm and strategic advice!"
    except Exception as e:
        print(f"❌ Error loading prompt: {e}")
        return "You are a Last Z strategy expert. Keep responses brief and helpful."

# Load single unified prompt at import time
SYSTEM_PROMPT = load_prompt_file("bot_prompt_v2.md")

# Tool function that GPT can call for regular knowledge search
def search_lastz_knowledge(user_query):
    """Search the Last Z knowledge base using vector embeddings"""
    start_time = time.time()
    
    try:
        print(f"🔧 Vector search tool called: '{user_query}'")
        
        # Create embedding for user query
        query_embedding = model.encode([user_query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, knowledge_embeddings)[0]
        
        # Get top results with similarity threshold
        similarity_threshold = 0.2
        top_indices = np.where(similarities >= similarity_threshold)[0]
        top_similarities = similarities[top_indices]
        
        # Sort by similarity
        sorted_pairs = sorted(zip(top_indices, top_similarities), key=lambda x: x[1], reverse=True)
        
        search_time = time.time() - start_time
        print(f"⚡ Vector search: {len(sorted_pairs)} results in {search_time:.2f}s (similarity {similarity_threshold}+)")
        
        if sorted_pairs:
            print(f"Top similarity: {sorted_pairs[0][1]:.3f}, Lowest: {sorted_pairs[-1][1]:.3f}")
        
        if len(sorted_pairs) > 3:
            print(f"📊 Large result set ({len(sorted_pairs)}), limiting to top 3 for point efficiency")
            sorted_pairs = sorted_pairs[:3]
        
        # Format results
        results = []
        for idx, similarity in sorted_pairs:
            if idx < len(knowledge_items):
                item = knowledge_items[idx]
                results.append({
                    "content": item["content"],
                    "title": item.get("title", "Knowledge Item"),
                    "similarity": float(similarity)
                })
        
        return {
            "query": user_query,
            "results": results,
            "total_found": len(sorted_pairs),
            "search_time": search_time
        }
        
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        return {
            "query": user_query,
            "error": str(e),
            "results": []
        }

# Load sentence transformer model and knowledge base
print("🤖 Loading sentence transformer model...")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    model = None

# Load and process knowledge base
print("🔍 Loading data from /app/data")
knowledge_items = []
knowledge_embeddings = None

def load_knowledge_base():
    """Load knowledge base from mounted data directory"""
    global knowledge_items, knowledge_embeddings
    
    try:
        # Use the existing knowledge loading logic from v0.7.9
        # This is a simplified version for the POC
        data_path = "/app/data"
        
        if not os.path.exists(data_path):
            print("❌ Data path not found")
            return
        
        # For POC, create some sample knowledge items
        knowledge_items = [
            {"title": "Sample Hero Data", "content": "Sample hero information for POC testing"},
            {"title": "Sample Building Data", "content": "Sample building information for POC testing"},
        ]
        
        if model:
            print("🧠 Creating embeddings for knowledge items...")
            embeddings_list = []
            for item in knowledge_items:
                embedding = model.encode(item["content"])
                embeddings_list.append(embedding)
            
            knowledge_embeddings = np.array(embeddings_list)
            print(f"✅ Created embeddings: {knowledge_embeddings.shape}")
        else:
            print("❌ Cannot create embeddings - model not loaded")
            
    except Exception as e:
        print(f"❌ Knowledge base loading error: {e}")

# Load knowledge base at startup
load_knowledge_base()

class LastZBot(fp.PoeBot):
    """Last Z Strategy Bot v0.8.0 - Data Collection POC"""
    
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
        
        # Available tools logging
        available_tools = ['search_lastz_knowledge', 'analyze_lastz_screenshot']
        print(f"🔧 Available tools: {available_tools}")
        
        # Simple knowledge search if query contains keywords
        if any(keyword in user_message.lower() for keyword in ['hero', 'build', 'upgrade', 'strategy']):
            tool_calls_made.append('search_lastz_knowledge')
            search_result = search_lastz_knowledge(user_message)
        
        # Create conversation for GPT
        conversation = [
            fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT),
        ]
        
        # Add user messages from request
        for msg in request.query:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                conversation.append(msg)
        
        # Create sanitized request like v0.7.9 does
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
            "GPT-5-Chat",
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
        
        # Store interaction data to Modal Volume
        store_interaction_data(interaction_data)

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5-Chat": 1},
            allow_attachments=True,           # ✅ Enable image uploads
            enable_image_comprehension=True,  # ✅ Auto image analysis
            introduction_message="🧪 Last Z Bot v0.8.0 Data Collection POC! 🎮 This version logs interactions for testing. Ask me anything about Last Z strategy! 🧟‍♂️💥"
        )

# Modal app setup with data collection POC
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data",
        remote_path="/app/data"
    )
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/poe-lastz-vector/prompts",
        remote_path="/app/prompts"
    )
)
app = App(f"poe-lastz-v0-8-0-poc-{deploy_hash}")

@app.function(
    image=image,
    cpu=4.0,  # 4 vCPUs for processing + data collection
    memory=8192,  # 8GB RAM for embeddings + logging
    min_containers=1,  # Keep 1 instance warm
    timeout=300,  # 5 minute timeout
    scaledown_window=600,  # Keep container alive 10 minutes
    volumes={"/app/storage": volume},  # Mount volume for data storage
    secrets=[
        modal.Secret.from_dict({
            "POE_ACCESS_KEY": "IpiGBRb3KqHt2sEdMRlaJ8Dt8C7SNIog",
            "POE_BOT_NAME": "LastzTest",
        })
    ],
)
@asgi_app()
def fastapi_app():
    bot = LastZBot()
    
    # Get credentials from environment (Modal secrets)
    bot_access_key = os.environ.get("POE_ACCESS_KEY")
    bot_name = os.environ.get("POE_BOT_NAME")
    
    print(f"🔐 Bot access key: {'✅ Found' if bot_access_key else '❌ Missing'}")
    print(f"🤖 Bot name: {bot_name}")
    
    app = fp.make_app(
        bot, 
        access_key=bot_access_key, 
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name)  # Allow fallback during development
    )
    
    return app