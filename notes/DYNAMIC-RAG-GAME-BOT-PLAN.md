# Dynamic RAG with Poe Server Bot Tools - Game Advice Bot

**Date**: October 10, 2025  
**Status**: Research Complete - Ready for Implementation

## 🎯 Core Discovery

**Poe server bots DO support tool calling** - specifically OpenAI-style function calling, which enables dynamic RAG implementations for game advice systems.

## 🔍 Key Findings

### ✅ Poe Tool Support Confirmed
- **OpenAI-compatible function calling** via `ToolDefinition` objects
- **Automatic tool execution** with `tool_executables` parameter  
- **Tool call streaming** with delta aggregation
- **Tool result handling** and response generation

### 📚 Available Components
- `ToolDefinition` - Define available functions (OpenAI format)
- `ToolCallDefinition` - Handle function calls from the model
- `ToolResultDefinition` - Return function results
- `stream_request()` with `tools` and `tool_executables` parameters

## 🎮 Proposed Game Advice Bot Architecture

### Tool 1: Game Detection & Source Selection
```python
async def select_game_sources(game_name: str, question_type: str) -> dict:
    """Dynamically select the best knowledge sources for a game"""
    game_sources = {
        "minecraft": {
            "wiki": "https://minecraft.wiki/",
            "guides": "https://minecraft-guides.com/",
            "api": "minecraft-api-endpoint"
        },
        "league_of_legends": {
            "wiki": "https://leagueoflegends.fandom.com/",
            "builds": "https://u.gg/",
            "patch_notes": "https://www.leagueoflegends.com/en-us/news/tags/patch-notes/"
        },
        "elden_ring": {
            "wiki": "https://eldenring.wiki.fextralife.com/",
            "builds": "https://eip.gg/elden-ring/",
            "maps": "https://mapgenie.io/elden-ring/"
        }
    }
    return game_sources.get(game_name.lower().replace(" ", "_"), {})
```

### Tool 2: Real-time Content Fetching
```python
async def fetch_game_content(source_url: str, search_terms: list[str]) -> str:
    """Fetch relevant content from game knowledge sources"""
    # Implement web scraping, API calls, or vector search
    # Return relevant game information
```

### Tool 3: Game-specific Data Lookup
```python
async def lookup_game_data(game: str, data_type: str, query: str) -> str:
    """Look up specific game data (items, characters, strategies)"""
    # Connect to game-specific databases or APIs
    # Return structured game information
```

## 🔄 Example Workflow

```
User: "What's the best build for Jinx in League of Legends?"

1. select_game_sources("League of Legends", "build") 
   → Returns LoL-specific sources
   
2. fetch_game_content(u.gg_url, ["Jinx", "build", "ADC"])
   → Gets current meta builds
   
3. lookup_game_data("lol", "champion_data", "Jinx")
   → Gets champion stats/abilities

Bot: Uses all this fresh data to give current, accurate advice
```

## 🚀 Advantages over Static RAG

| Feature | Static RAG | Dynamic RAG with Tools |
|---------|------------|------------------------|
| **Data Freshness** | ❌ Outdated | ✅ Real-time updates |
| **Game Coverage** | ❌ Pre-configured only | ✅ Expandable to any game |
| **Source Flexibility** | ❌ Fixed sources | ✅ Dynamic source selection |
| **Context Awareness** | ❌ Generic | ✅ Game & question-type specific |
| **Maintenance** | ❌ Manual updates | ✅ Self-updating |

## 🛠️ Implementation Benefits

1. **Dynamic Source Selection**: Tools choose the right knowledge base per game
2. **Real-time Updates**: Fetch current patch notes, meta changes, guides  
3. **Multi-source Integration**: Combine wikis, databases, community guides
4. **Context-Aware**: Different tools for different question types (builds vs. lore vs. mechanics)
5. **Scalable**: Easy to add new games and sources
6. **Always Current**: No stale information

## 📋 MCP vs Poe Tools Comparison

| Feature | MCP Tools | Poe Server Bot Tools |
|---------|-----------|---------------------|
| **Protocol** | Model Context Protocol | OpenAI Function Calling |
| **Support** | ❌ Not directly | ✅ Native support |
| **Format** | MCP schema | OpenAI schema |
| **Integration** | Would need bridge | Direct integration |
| **Maturity** | Newer standard | Established, well-documented |

## 🎯 Next Steps

### Phase 1: Basic Tool Implementation
1. Create enhanced bot with tool calling
2. Implement game detection tool
3. Add basic content fetching tool
4. Test with 1-2 popular games

### Phase 2: Advanced Features  
1. Add multiple knowledge source types
2. Implement intelligent source ranking
3. Add caching for performance
4. Support for more game types

### Phase 3: Production Ready
1. Error handling and fallbacks
2. Rate limiting and API management
3. User preference learning
4. Performance optimization

## 💡 Key Insight

**This approach is superior to traditional RAG** because it's:
- **Adaptive**: Changes based on context
- **Current**: Always pulls fresh data
- **Comprehensive**: Multiple source types
- **Intelligent**: Context-aware decisions

## 📁 Current Project Status

- ✅ Poe server bot deployed and working (PeteRepeat)
- ✅ Modern development environment (Ruff, dev container)
- ✅ Tool calling capability confirmed
- 🎯 **Ready to implement game advice bot with dynamic RAG**

## 🔗 Reference Links

- **Poe Protocol Specification**: https://creator.poe.com/docs/server-bots/poe-protocol-specification  
- **FastAPI-Poe Library**: https://pypi.org/project/fastapi-poe/
- **Current Bot Deployment**: https://bcoughlin--poe-echo-bot-serve.modal.run
- **Project Repository**: Current workspace with complete dev setup

---

**Ready to resume implementation when you return!** 🚀