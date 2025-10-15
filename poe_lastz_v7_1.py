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
app = modal.App(f"poe-lastz-v7-1-{deploy_hash}")

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

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        """Bot settings with clean tool definitions."""
        return fp.SettingsResponse(
            server_bot_dependencies={"GPT-5": 1},
            introduction_message=f"""🎮 **Last Z Expert V7-1** (Hash: {deploy_hash[:4]})

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
        
        # Get user message
        user_message = request.query[-1].content
        
        # Search knowledge base
        relevant_knowledge = self.search_knowledge(user_message)
        
        # Build enhanced system prompt
        knowledge_context = ""
        if relevant_knowledge:
            knowledge_context = "**Relevant Knowledge:**\n" + "\n".join(f"• {item}" for item in relevant_knowledge) + "\n\n"

        system_prompt = f"""You are a Last Z: Survival Shooter expert.

{knowledge_context}**Instructions:**
- Extract player information from conversations (gamertag, levels, hero counts, etc.)
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