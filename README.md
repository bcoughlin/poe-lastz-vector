# Last Z Vector RAG Bot

A Poe bot for Last Z: Survival Shooter using vector-based Retrieval Augmented Generation with dynamic data loading from Render disk.

## What This Bot Does

The Last Z bot is your strategic gaming companion for Last Z: Survival Shooter. It helps players:

- **Analyze hero screenshots** and provide specific upgrade advice based on stats and level
- **Compare heroes** with detailed stat growth tables and strategic recommendations
- **Optimize building progression** for headquarters, research facilities, and defensive structures
- **Plan resource allocation** for maximum efficiency in upgrades and recruitment
- **Answer strategic questions** using a comprehensive knowledge base of 135+ game items
- **Provide PvP and PvE tactics** tailored to your current game state and goals

The bot uses semantic search through game data to give accurate, specific advice rather than generic gaming tips. It can identify heroes from screenshots, explain complex game mechanics, and help you make data-driven decisions about where to invest your time and resources.

**Bot Personality**: Cool, knowledgeable gamer who explains things naturally without hype - like that friend who's really good at games but doesn't show off about it.

## Technical Features

- **Dynamic Knowledge Loading**: Automatically loads data from Render disk at startup, not build time
- **Vector Search**: Semantic search with OpenAI embeddings for intelligent content matching
- **Anti-Hallucination**: Debug footer showing sources + strengthened system prompts with deny lists
- **Disk-Cached Embeddings**: Persistent across restarts for fast startup (no re-processing)
- **Dynamic Version Loading**: Automatic detection and loading of latest bot version

## Technical Innovations

### Render Deployment Architecture
- **Build vs Runtime Separation**: Data loading happens at app startup, not during build phase
- **External Data Sync**: Pulls latest game data from external repository during deployment
- **Disk Mount Integration**: Leverages Render's persistent disk storage for knowledge base
- **Zero-Config Version Management**: New versions auto-detected without deployment changes

### RAG Pipeline Optimizations
- **Semantic Query Enhancement**: User queries enriched with game context before vector search
- **Knowledge Base Caching**: Pre-computed embeddings stored on disk, loaded once per deployment
- **Multi-Modal Analysis**: Screenshot analysis combined with knowledge base lookups
- **Structured Data Delivery**: Complete JSON objects sent to LLM for precise stat comparisons

### Anti-Hallucination Measures
- **Source Attribution**: Every response shows which knowledge base items were used
- **Fake Hero Deny List**: Explicit prevention of common AI-generated hero names
- **Knowledge Base Boundaries**: Strict limits on what data can be referenced
- **Graceful Degradation**: Clear messaging when data isn't available vs making up information

### Performance Features
- **FastAPI Async**: Non-blocking request handling for concurrent users
- **Embedding Persistence**: Avoids re-computing vectors on every restart
- **Smart Caching**: Knowledge base loaded once, served to multiple requests
- **Minimal Dependencies**: Optimized for fast cold starts on Render

## Quick Links

- 📐 **[ARCHITECTURE.md](ARCHITECTURE.md)** - Project structure, module design, dynamic loading pattern
- 📝 **[notes/](notes/)** - Historical planning documents and development notes

## Development Setup

### 1. Install Dependencies
```bash
make install
# or
pip install -r requirements_render.txt
```

### 2. Setup Git Hooks (Recommended)
Automatically runs linting checks before each commit:
```bash
bash scripts/setup-hooks.sh
```

### 3. Development Commands
```bash
make help           # Show all available commands
make lint          # Run linting checks
make lint-fix      # Auto-fix linting issues
make format        # Format code with ruff
make check         # Run all pre-commit checks
make clean         # Clean up cache files
```

## Deployment

### Production (Render)
The bot is deployed to Render with automatic data syncing:

```bash
# Render automatically runs on deploy:
bash sync_data.sh && python -m uvicorn server_entry:app --host 0.0.0.0 --port $PORT
```

**Current version**: v0.8.2 via dynamic server loading

**Production URL**: https://poe-lastz-v0-8-1.onrender.com

See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the symlink versioning pattern and how to switch versions.

## Project Structure

```
poe-lastz-vector/
├── server_entry.py       # Dynamic version loader & entry point
├── poe_lastz_v0_8_2/     # Current production code
│   ├── server.py         # Main FastAPI app
│   ├── knowledge_base.py # Data loading & vector search
│   ├── logger.py         # Interaction logging
│   └── prompts.py        # System prompts & bot personality
├── Makefile              # Development commands
└── scripts/              # Setup scripts
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the dynamic loading pattern and version management.

## Troubleshooting

- **Import errors**: Check `server_entry.py` can detect latest version directory
- **Linting errors**: Run `make lint-fix` to auto-fix most issues
- **Data loading fails**: Check `sync_data.sh` executed successfully and `/mnt/data` mounted
- **Embeddings cache errors**: Delete `embeddings_cache.pkl` and restart
