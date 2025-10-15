# LastZ Bot V7.6 Architecture - Semantic Search with Tool Calling

## Overview

LastZ Bot V7.6 represents a significant architectural evolution from specific data handlers to semantic search across all game knowledge. This version uses natural language processing to find relevant information from heroes, buildings, equipment, and strategy data without requiring explicit categorization.

## Architecture Components

### 1. Data Loading & Processing (`LastZVectorSearch`)

```python
class LastZVectorSearch:
    def __init__(self):
        self.knowledge_items = []  # In-memory knowledge base
        self._load_all_data()      # Load at startup
```

**Data Sources:**
- `/app/data/heroes/*.json` - Individual hero files
- `/app/data/buildings.json` - Structured building data
- `/app/data/equipment.json` - Equipment items and stats

**Processing Pipeline:**
1. **Load JSON files** from mounted Modal directory
2. **Extract searchable text** from each item (name, role, description, stats)
3. **Create knowledge items** with type, name, searchable text, and full data
4. **Store in memory** for fast search access

### 2. Search Engine (Simple Text Matching)

```python
def simple_text_search(self, query: str, max_results: int = 5) -> List[Dict]:
    # Keyword-based scoring with name matching priority
    # Future: Replace with vector embeddings
```

**Current Implementation:**
- **Keyword matching** in item text
- **Name priority scoring** (exact name matches get higher scores)
- **Relevance ranking** by cumulative keyword matches
- **Result limiting** to top 5 most relevant items

**Future Enhancement Path:**
- Replace with actual vector embeddings (OpenAI, sentence-transformers)
- Implement cosine similarity search
- Add semantic understanding beyond keyword matching

### 3. Tool Calling Interface

```python
def search_lastz_knowledge(user_query: str) -> str:
    """Single tool for all game knowledge searches"""
    results = vector_search.simple_text_search(user_query)
    return json.dumps(formatted_results)
```

**Key Features:**
- **Natural language input** - pass user's exact question
- **Cross-domain search** - finds relevant data across all categories
- **Structured output** - JSON with results, scores, and full data
- **GPT-friendly format** - easy for GPT to parse and present

### 4. Modal Deployment Architecture

```python
# Local data mounting
.add_local_dir("/Users/bradleycoughlin/local_code/lastz-rag/data", remote_path="/app/data")

# Dependencies for future vector search
REQUIREMENTS = ["fastapi-poe", "numpy", "scikit-learn"]
```

**Benefits:**
- **Local development** - data changes reflect immediately
- **No volume complexity** - simpler than Modal volumes
- **Embedding ready** - numpy/sklearn for future vector implementation

## Data Flow

### 1. Startup Sequence
```
Modal App Start → Mount /app/data → Load JSON files → 
Create searchable text → Build knowledge_items → Ready for queries
```

### 2. Query Processing
```
User Question → GPT determines need for data → 
Calls search_lastz_knowledge(user_query) → 
Keyword search → Ranked results → 
JSON response → GPT formats for user
```

### 3. Response Architecture
```python
{
  "query": "best heroes for early game",
  "results_count": 3,
  "results": [
    {
      "type": "hero",
      "name": "Natalie", 
      "summary": "Hero: Natalie Role: Support Rarity: B-Blue...",
      "full_data": { /* complete hero JSON */ }
    }
  ]
}
```

## Advantages Over V7.5

### V7.5 (Specific Handlers)
- ❌ Required query type categorization ("heroes", "buildings")
- ❌ Rigid if/elif structure for each data type
- ❌ GPT had to choose correct handler
- ❌ Limited cross-domain searches

### V7.6 (Semantic Search)
- ✅ Natural language queries ("best early game heroes")
- ✅ Single flexible search tool
- ✅ Cross-domain results (heroes + strategy tips)
- ✅ Future-ready for vector embeddings

## Example Query Comparisons

### V7.5 Approach:
```
User: "Which heroes work well with headquarters level 5?"
GPT: Must categorize as "heroes" → get_lastz_data("heroes") → 
Only hero data returned → Limited context
```

### V7.6 Approach:
```
User: "Which heroes work well with headquarters level 5?"
GPT: Pass exact query → search_lastz_knowledge("Which heroes work well with headquarters level 5?") →
Returns: Hero data + HQ scaling info + relevant strategy notes
```

## Future Enhancement Roadmap

### Phase 1: True Vector Embeddings
```python
# Replace simple_text_search with:
from sentence_transformers import SentenceTransformer

def vector_search(self, query: str):
    query_embedding = self.model.encode(query)
    similarities = cosine_similarity([query_embedding], self.item_embeddings)
    return ranked_results
```

### Phase 2: Contextual Understanding
- **Multi-turn conversations** - remember previous context
- **Follow-up questions** - "What about their late game potential?"
- **Comparative queries** - "Compare Natalie vs Fiona for support"

### Phase 3: Dynamic Knowledge Updates
- **Real-time data updates** - game balance changes
- **User-contributed content** - strategy guides, tips
- **Personalized recommendations** - based on player level/style

## Performance Characteristics

### Memory Usage
- **Startup**: ~5MB for 45 knowledge items
- **Search**: O(n) keyword matching across all items
- **Scaling**: Linear with knowledge base size

### Response Time
- **Cold start**: ~2-3 seconds (data loading)
- **Warm queries**: ~100-500ms (in-memory search)
- **GPT processing**: ~2-5 seconds (tool calling + response generation)

### Scalability Limits
- **Current**: Good for ~1000 knowledge items
- **Bottleneck**: Linear search across all items
- **Solution**: Vector database (Pinecone, Weaviate) for larger datasets

## Deployment Configuration

### Current Setup
```python
app = App(f"poe-lastz-v7-6-embeddings-{deploy_hash}")
URL: https://bcoughlin--poe-lastz-v7-6-embeddings-5754b2-fastapi-app.modal.run
```

### Production Considerations
- **Memory limits**: Monitor knowledge base growth
- **Search optimization**: Implement vector embeddings for scale
- **Error handling**: Graceful degradation when data loading fails
- **Monitoring**: Track search relevance and user satisfaction

## Development Status

### ✅ Working Features
- Local data mounting and loading
- Cross-domain semantic search (45 knowledge items loaded)
- Natural language tool calling
- Structured JSON responses
- GPT integration with tool_executables

### 🔧 Known Issues
- Hero skills processing errors (dict vs string format)
- Simple keyword matching (not true semantic search yet)
- No result relevance scoring beyond keyword count

### 🎯 Next Priorities
1. Fix hero skills data parsing
2. Implement true vector embeddings
3. Add result relevance scoring
4. Enhanced error handling and logging

## Comparison Matrix

| Feature | V7.5 Handlers | V7.6 Semantic | Future V7.7+ |
|---------|---------------|---------------|--------------|
| Query Type | Categorized | Natural Language | Conversational |
| Search Scope | Single Domain | Cross-Domain | Contextual |
| Flexibility | Rigid | Flexible | Adaptive |
| Setup Complexity | Medium | Low | Low |
| Search Quality | Exact Match | Keyword Match | Semantic Match |
| Scalability | Good | Medium | Excellent |

This architecture provides a strong foundation for intelligent game assistance while maintaining simplicity and clear upgrade paths for future enhancements.