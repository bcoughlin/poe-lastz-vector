#!/usr/bin/env python3
"""
Last Z Bot v0.8.2 - Enhanced Knowledge Delivery with Full JSON Data
- Sends complete structured data (stats, progression, costs) to LLM
- Better handling of hero/building/research queries with precise info
- Maintains disk-based embedding cache for performance
"""

import hashlib
import json
import logging
import os
import time
from collections.abc import AsyncIterator
from datetime import datetime

import openai

import fastapi_poe as fp
from bot_symlink import knowledge_base

# Import utility modules
from bot_symlink.logger import (
    create_interaction_log,
    download_and_store_image,
    log_interaction_to_console,
    store_interaction_data,
)
from bot_symlink.prompts import load_system_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
deploy_time = datetime.now().strftime("%Y-%m-%d %H:%M")

print(f"🚀 Last Z Bot v0.8.2 Render - {deploy_time}")
print(f"🔑 Deploy hash: {deploy_hash}")

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
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"❌ OpenAI client initialization failed: {e}")
    raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

# Cache for pre-computed embeddings (populated at startup)
knowledge_embeddings = {}


# OLD DUPLICATE CODE REMOVED - now using imports from logger.py and prompts.py
# The following were deleted:
# - Data storage configuration (now in logger.py)
# - create_interaction_log() (now in logger.py)
# - log_interaction_to_console() (now in logger.py)
# - store_interaction_data() (now in logger.py)
# - download_and_store_image() (now in logger.py)
# - load_system_prompt() (now in prompts.py)

# EMBEDDINGS AND SEARCH FUNCTIONS START HERE


def cosine_similarity(a, b):
    """Simple cosine similarity calculation"""
    import math

    dot_product = sum(x * y for x, y in zip(a, b, strict=False))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0
    return dot_product / (magnitude_a * magnitude_b)


def get_openai_embedding(text: str) -> list[float]:
    """Get embedding from OpenAI API"""
    try:
        if not openai_client:
            print("❌ OpenAI client not available")
            return []
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",  # Cost-effective model
            input=text,
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
        "/tmp/embeddings_cache.json",  # Fallback for local dev
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
    for item in sorted(knowledge_base.knowledge_items, key=lambda x: x.get("name", "")):
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
        with open(cache_path) as f:
            cache_data = json.load(f)

        # Verify cache is valid for current knowledge base
        cached_hash = cache_data.get("knowledge_hash", "")
        current_hash = calculate_knowledge_hash()

        if cached_hash != current_hash:
            print("⚠️  Cache invalid - knowledge base changed (hash mismatch)")
            print(f"   Cached: {cached_hash[:8]}... Current: {current_hash[:8]}...")
            return False

        knowledge_embeddings = cache_data.get("embeddings", {})
        cache_version = cache_data.get("version", "unknown")

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
            "version": "0.8.1",
            "timestamp": datetime.now().isoformat(),
            "knowledge_hash": calculate_knowledge_hash(),
            "embeddings_count": len(knowledge_embeddings),
            "embeddings": knowledge_embeddings,
        }

        print(f"💾 Saving embeddings cache to {cache_path}")
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)

        # Get file size for logging
        file_size = os.path.getsize(cache_path) / (1024 * 1024)  # MB
        print(
            f"✅ Saved {len(knowledge_embeddings)} embeddings to disk ({file_size:.2f} MB)"
        )

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
    print(
        f"🔄 Generating embeddings for {len(knowledge_base.knowledge_items)} knowledge items..."
    )
    print("   (This only happens when knowledge base changes)")
    start_time = time.time()

    for idx, item in enumerate(knowledge_base.knowledge_items):
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
            print(
                f"   ⏳ Progress: {idx + 1}/{len(knowledge_base.knowledge_items)} items embedded..."
            )

    elapsed_time = time.time() - start_time
    print(f"✅ Generated {len(knowledge_embeddings)} embeddings in {elapsed_time:.2f}s")
    if len(knowledge_embeddings) > 0:
        print(
            f"   Average: {elapsed_time / len(knowledge_embeddings):.3f}s per embedding"
        )
    else:
        print("   ⚠️ No embeddings generated - knowledge_items appears to be empty")

    # Save to disk for next restart
    save_embeddings_to_disk()


def search_lastz_knowledge(user_query):
    """Search using OpenAI embeddings with comprehensive knowledge base"""
    start_time = time.time()

    try:
        print(f"🔧 OpenAI embedding search called: '{user_query}'")
        print(
            f"📚 Searching {len(knowledge_base.knowledge_items)} knowledge items using cached embeddings"
        )

        # Get embedding for user query (only 1 API call per query)
        query_embedding = get_openai_embedding(user_query)
        if not query_embedding:
            return {
                "query": user_query,
                "error": "Failed to get embedding for query",
                "results": [],
            }

        results = []

        # Calculate similarity with each knowledge item using cached embeddings
        for idx, item in enumerate(knowledge_base.knowledge_items):
            # Generate the same key used during pre-computation
            item_key = (
                f"{item.get('type', 'unknown')}_{item.get('name', 'unnamed')}_{idx}"
            )

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
                if item_type in [
                    "hero",
                    "research",
                    "building",
                    "equipment",
                ] and isinstance(item_data, dict):
                    # Format structured JSON data for LLM consumption
                    content = json.dumps(item_data, indent=2)
                else:
                    # For markdown/text content, use the text or content field
                    searchable_text = item.get("text", "")
                    content = searchable_text
                    if "content" in item_data:
                        content = item_data["content"][
                            :1000
                        ]  # Increased limit for better context

                results.append(
                    {
                        "content": content,
                        "title": item.get("name", "Unknown"),
                        "type": item_type,
                        "similarity": similarity,
                        "is_structured": item_type
                        in ["hero", "research", "building", "equipment"],
                    }
                )

        # Sort by similarity and limit results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:5]  # Increased from 3 to 5 for better context

        search_time = time.time() - start_time
        print(
            f"⚡ OpenAI embedding search: {len(results)} results in {search_time:.2f}s (using cache)"
        )
        if results:
            print(
                f"   Top result: {results[0]['title']} (similarity: {results[0]['similarity']:.3f})"
            )

        return {
            "query": user_query,
            "results": results,
            "total_found": len(results),
            "search_time": search_time,
        }

    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback

        traceback.print_exc()
        return {"query": user_query, "error": str(e), "results": []}


class LastZBot(fp.PoeBot):
    """Last Z Strategy Bot v0.8.1 - Render Hosted Data Collection POC"""

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterator[fp.PartialResponse]:
        start_time = time.time()

        # Extract request information for data collection
        user_id = getattr(request, "user_id", "unknown")
        conversation_id = getattr(request, "conversation_id", "unknown")
        message_id = getattr(request, "message_id", "unknown")

        # Get user message and check for images
        user_message = ""
        has_images = False
        image_count = 0
        image_data = []

        if request.query:
            latest_message = request.query[-1]
            print("🔍 Message structure debug:")
            print(f"   - Has content attr: {hasattr(latest_message, 'content')}")
            print(
                f"   - Content type: {type(getattr(latest_message, 'content', None))}"
            )
            print(
                f"   - Has attachments attr: {hasattr(latest_message, 'attachments')}"
            )

            if hasattr(latest_message, "content"):
                if isinstance(latest_message.content, str):
                    user_message = latest_message.content
                    print(f"   - String content: {user_message[:100]}...")
                elif isinstance(latest_message.content, list):
                    print(f"   - List content with {len(latest_message.content)} items")
                    # Handle content array (text + images)
                    text_parts = []
                    for i, content_part in enumerate(latest_message.content):
                        print(f"     Content part {i}: {type(content_part)}")
                        if hasattr(content_part, "type"):
                            print(f"       Type: {content_part.type}")
                            if content_part.type == "text":
                                text_parts.append(content_part.text)
                                print(f"       Text: {content_part.text}")
                            elif content_part.type == "image_url":
                                has_images = True
                                image_count += 1
                                print("       ✅ IMAGE DETECTED!")
                        else:
                            print(f"       No type attribute: {dir(content_part)}")
                    user_message = " ".join(text_parts)

            # Also check for attachments and extract detailed info
            if hasattr(latest_message, "attachments") and latest_message.attachments:
                print(f"   - Attachments found: {len(latest_message.attachments)}")
                for i, attachment in enumerate(latest_message.attachments):
                    print(f"     Attachment {i}: {type(attachment)}")

                    # Extract attachment data
                    attachment_info = {
                        "index": i,
                        "content_type": getattr(attachment, "content_type", None),
                        "name": getattr(attachment, "name", None),
                        "url": getattr(attachment, "url", None),
                        "size": getattr(attachment, "size", None),
                        "parsed_content": getattr(attachment, "parsed_content", None),
                    }

                    # Log all available attributes for debugging
                    print(f"       Content Type: {attachment_info['content_type']}")
                    print(f"       Name: {attachment_info['name']}")
                    print(f"       URL: {attachment_info['url']}")
                    print(f"       Size: {attachment_info['size']}")

                    image_data.append(attachment_info)
                    has_images = True
                    image_count += 1

        print(
            f"🔧 Processing query with {len(request.query)} messages, has_images: {has_images}"
        )

        # Track tool calls for data collection
        tool_calls_made = []

        # ALWAYS run knowledge search for every query to prevent hallucinations
        search_result = None
        print(f"🔎 Running knowledge base search for: {user_message[:100]}...")
        tool_calls_made.append("search_lastz_knowledge")
        search_result = search_lastz_knowledge(user_message)
        print(f"🔍 Search found {len(search_result.get('results', []))} results")

        # Create conversation for GPT
        conversation = [
            fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT),
        ]

        # Add search results if available - ENHANCED FOR v0.8.2
        if search_result and search_result.get("results"):
            knowledge_context = "=== KNOWLEDGE BASE SEARCH RESULTS ===\n"
            knowledge_context += "⚠️ CRITICAL: You MUST base your answer ONLY on the information below. DO NOT add information from your general knowledge or training data.\n"
            knowledge_context += "⚠️ If the user asks about something NOT in these results, say 'I don't have information about that in my knowledge base.'\n\n"

            for idx, result in enumerate(
                search_result["results"][:3], 1
            ):  # Top 3 results
                knowledge_context += f"📄 SOURCE {idx}: {result['title']} (type: {result['type']}, relevance: {result['similarity']:.2f})\n"

                # For structured data, provide clear formatting
                if result.get("is_structured"):
                    knowledge_context += "   STRUCTURED DATA (JSON):\n"
                    # Indent the JSON for readability
                    for line in result["content"].split("\n"):
                        knowledge_context += f"   {line}\n"
                else:
                    # For text/markdown content
                    knowledge_context += f"   {result['content'][:1000]}...\n"

                knowledge_context += "\n"

            knowledge_context += "⚠️ REMINDER: Only use information from the sources above. Do not invent stats, names, or mechanics.\n"

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
            if hasattr(msg, "role") and hasattr(msg, "content"):
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
            temperature=0.6,  # Balanced temperature for factual yet friendly responses
        )

        # Collect bot response for logging
        bot_response_parts = []

        async for msg in fp.stream_request(
            sanitized_request,
            "GPT-5-Chat",  # Use GPT-5-Chat for Poe platform
            request.access_key,
        ):
            if hasattr(msg, "text") and msg.text:
                bot_response_parts.append(msg.text)
            yield msg

        # Add debug footer showing sources used (helps detect hallucinations)
        if search_result and search_result.get("results"):
            source_names = [r["title"] for r in search_result["results"][:3]]
            footer = f"\n\n*📚 Sources: {', '.join(source_names)}*"
            yield fp.PartialResponse(text=footer)
        else:
            footer = "\n\n*⚠️ No knowledge base sources found for this query*"
            yield fp.PartialResponse(text=footer)

        # Calculate response time and create interaction log
        response_time = time.time() - start_time
        bot_response = "".join(bot_response_parts)

        # Try to download and store images if URLs are available
        for img_info in image_data:
            if img_info.get("url") and img_info.get("name"):
                try:
                    stored_path = download_and_store_image(
                        img_info["url"], img_info["name"], user_id, message_id
                    )
                    if stored_path:
                        img_info["stored_path"] = stored_path
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
            response_time=response_time,
        )

        # Log to console for POC testing
        log_interaction_to_console(interaction_data)

        # Store interaction data to filesystem
        store_interaction_data(interaction_data)

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={
                "GPT-5-Chat": 1
            },  # Using GPT-5-Chat for Poe platform
            allow_attachments=True,  # ✅ Enable image uploads
            enable_image_comprehension=True,  # ✅ Auto image analysis
            introduction_message="🎮 Hey there! I'm your Last Z: Survival Shooter strategy expert! �‍♂️💥\n\nI can help you with:\n• Hero strategies & team builds 🦸‍♀️\n• Base building & upgrades 🏰\n• Research priorities 🔬\n• Combat tactics ⚔️\n• Screenshot analysis �\n\nDrop your questions or share screenshots - let's dominate the apocalypse together! 🔥",
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
    print("🏠 Hosting: Render")

    # Note: Not passing bot_name to fp.make_app to avoid "asyncio.run() cannot be called
    # from a running event loop" error during startup. Bot settings can be synced manually
    # using the sync_settings.py script if needed. The bot still works without auto-sync.
    app = fp.make_app(
        bot,
        access_key=bot_access_key,
        allow_without_key=not bot_access_key,  # Allow fallback during development
    )

    return app


# Create the FastAPI app instance
app = create_app()


@app.on_event("startup")
async def startup_event():
    """Load knowledge base after app starts (when disk is mounted)"""
    print("🚀 App startup - loading knowledge base...")
    knowledge_base.load_knowledge_base()
    print(f"✅ Knowledge base loaded - {len(knowledge_base.knowledge_items)} items")

    # Pre-compute embeddings for all knowledge items (one-time cost at startup)
    print("🔄 Pre-computing embeddings for knowledge base...")
    precompute_knowledge_embeddings()
    print(
        f"✅ Startup complete - {len(knowledge_base.knowledge_items)} items with {len(knowledge_embeddings)} cached embeddings"
    )


# Health check endpoint for Render
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.8.2",
        "hosting": "render",
        "timestamp": datetime.now().isoformat(),
        "deploy_hash": deploy_hash,
        "knowledge_items": len(knowledge_base.knowledge_items),
        "cached_embeddings": len(knowledge_embeddings),
        "enhancements": "Full JSON data delivery for structured content",
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
            timeout=30,
        )

        if result.returncode == 0:
            # Reload knowledge base
            old_count = len(knowledge_base.knowledge_items)
            old_embeddings = len(knowledge_embeddings)

            knowledge_base.load_knowledge_base()
            new_count = len(knowledge_base.knowledge_items)

            # CRITICAL: Regenerate embeddings for new/changed data
            print("🔄 Regenerating embeddings after data refresh...")
            precompute_knowledge_embeddings()
            new_embeddings = len(knowledge_embeddings)

            return {
                "status": "success",
                "git_output": result.stdout,
                "knowledge_items": {
                    "old": old_count,
                    "new": new_count,
                    "changed": new_count - old_count,
                },
                "embeddings": {
                    "old": old_embeddings,
                    "new": new_embeddings,
                    "regenerated": new_embeddings > 0,
                },
                "timestamp": datetime.now().isoformat(),
            }
        else:
            return {
                "status": "error",
                "git_error": result.stderr,
                "returncode": result.returncode,
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
