# Architecture Documentation

## Project Overview

This is a Poe bot for Last Z: Survival Shooter using vector-based RAG (Retrieval Augmented Generation) with dynamic data loading from Render disk.

## Directory Structure

```
poe-lastz-vector/
├── README.md                    # Main documentation (setup, deployment)
├── ARCHITECTURE.md              # This file (structure, patterns)
├── bot_symlink/                 # Symlink → poe_lastz_v0_8_2/
├── poe_lastz_v0_8_2/           # Current active version
│   ├── server.py               # Main bot (1207 lines → refactoring in progress)
│   ├── knowledge_base.py       # Knowledge loading (427 lines) ✅
│   ├── logger.py               # Interaction logging (118 lines) ✅
│   ├── prompts.py              # System prompt loading (53 lines) ✅
│   └── __init__.py
├── scripts/
│   └── setup-hooks.sh          # Git hooks installer
├── Makefile                    # Development commands
├── notes/                      # Historical planning docs
└── requirements_render.txt
```

## Bot Version Symlink Pattern

### Why Use a Symlink?

The `bot_symlink` → `poe_lastz_v0_8_2/` pattern provides:

- **No deployment config changes**: `render.yaml` always uses `bot_symlink.server:app`, never needs editing
- **Easy version switching**: Just update the symlink to point to a different version
- **Clear indication**: The symlink name makes it obvious which version is active
- **Zero downtime**: Change symlink, commit, push → Render deploys new version

### Current Setup

```bash
bot_symlink -> poe_lastz_v0_8_2/
```

### Switching Versions

When you want to deploy a different version (e.g., `poe_lastz_v0_8_3`):

```bash
# Remove old symlink
rm bot_symlink

# Create new symlink to the new version
ln -s poe_lastz_v0_8_3 bot_symlink

# Commit the change
git add bot_symlink
git commit -m "Switch to v0.8.3"
git push
```

### Verification

```bash
ls -la bot_symlink
# Output: bot_symlink -> poe_lastz_v0_8_2
```

## Module Architecture

### Current Modules (v0.8.2)

#### knowledge_base.py (427 lines) ✅
**Purpose**: Load and parse game knowledge from lastz-rag data repository

**Functions**:
- `load_knowledge_base()` - Main loading function with stats
- `_parse_data_index()` - Parses data_index.md configuration
- `_load_from_data_index()` - Loads based on config
- `_load_json_directory()`, `_load_markdown_directory()` - Directory loaders
- `_process_hero_file()`, `_process_research_file()`, etc. - Data processors
- `_load_legacy_hardcoded()` - Fallback loader

**Global State**: `knowledge_items = []` (shared list)

#### logger.py (118 lines) ✅
**Purpose**: Interaction logging and data collection

**Functions**:
- `create_interaction_log()` - Structures interaction data
- `log_interaction_to_console()` - Console logging
- `store_interaction_data()` - Filesystem storage
- `download_and_store_image()` - Image handling

#### prompts.py (53 lines) ✅
**Purpose**: System prompt loading with fallback

**Functions**:
- `load_system_prompt()` - Loads prompt from multiple paths with anti-hallucination fallback

#### server.py (1207 lines) 🔄 REFACTORING IN PROGRESS
**Current Contents**:
- Lines 1-638: Imports, environment setup, config
- Lines 639-871: Embeddings and search functions (→ embeddings.py)
- Lines 872+: LastZBot class, FastAPI setup (→ bot.py)

**Target**: ~230 lines (entry point only)

### Planned Extractions

#### embeddings.py (~250 lines) 📋 PLANNED
**Purpose**: Vector embeddings and semantic search

**Functions to extract from server.py (lines 639-871)**:
- `cosine_similarity()` - Similarity calculation
- `get_openai_embedding()` - OpenAI API wrapper
- `get_embeddings_cache_path()` - Disk cache path
- `calculate_knowledge_hash()` - Cache invalidation
- `load_embeddings_from_disk()` - Persistent cache loading
- `save_embeddings_to_disk()` - Persistent cache saving
- `precompute_knowledge_embeddings()` - Embedding generation
- `search_lastz_knowledge()` - Semantic search

**Global State**: `knowledge_embeddings = {}`

**Dependencies**: Imports `knowledge_items` from `knowledge_base`

#### bot.py (~300 lines) 📋 PLANNED
**Purpose**: Poe bot implementation and FastAPI setup

**Contents to extract from server.py (lines 872+)**:
- `LastZBot` class (full implementation)
- FastAPI app creation
- Health check endpoints
- Bot initialization logic

**Dependencies**: Imports from `knowledge_base`, `embeddings`, `logger`, `prompts`

### Final Structure (After Extraction)

```
poe_lastz_v0_8_2/
├── server.py           # Entry point (~230 lines)
├── knowledge_base.py   # Data loading (427 lines) ✅
├── embeddings.py       # Vector search (~250 lines) 📋
├── bot.py             # Bot + FastAPI (~300 lines) 📋
├── logger.py          # Logging (118 lines) ✅
├── prompts.py         # Prompts (53 lines) ✅
└── __init__.py
```

Each file: **~250 lines max** → Faster linting, easier debugging, cleaner git diffs

## Features (v0.8.2)

- ✅ Full JSON data delivery for structured content (heroes, buildings, research)
- ✅ Anti-hallucination measures with debug footer showing sources
- ✅ Temperature set to 0.6 for balanced responses
- ✅ Disk-based embedding cache (persistent across restarts)
- ✅ GitHub Actions auto-refresh on data changes
- ✅ Admin refresh endpoint with embedding regeneration

## Development Workflow

### Setup
```bash
make install          # Install dependencies
bash scripts/setup-hooks.sh  # Install git hooks
```

### Daily Commands
```bash
make lint            # Run linting checks
make lint-fix        # Auto-fix linting issues
make format          # Format code with ruff
make check           # Run all pre-commit checks
make clean           # Clean up cache files
```

### Git Hooks
Pre-commit hook automatically runs:
1. `ruff check` - Linting
2. `ruff format --check` - Format validation

Can bypass with `--no-verify` if needed.

### Extraction Process
When extracting new modules:
1. Identify clear boundaries (use `grep -n "^def \|^class " server.py`)
2. Create new file with extracted functions
3. Update imports in server.py
4. Run `make check` to verify
5. Test with `python -c "import bot_symlink.server"`
6. Commit with descriptive message

## Deployment

### Render Production
- **Service**: `poe-lastz-v0-8-1` (will update to v0-8-2)
- **Entry point**: `bot_symlink.server:app`
- **Start command**: `bash sync_data.sh && python -m uvicorn bot_symlink.server:app --host 0.0.0.0 --port $PORT`
- **URL**: https://poe-lastz-v0-8-1.onrender.com

### Data Loading
Data synced from `lastz-rag` repository to Render disk at startup via `sync_data.sh`.

## Design Principles

1. **Modular architecture**: Each file has single responsibility
2. **Symlink versioning**: Easy version switching without config changes
3. **Fail fast, no silent fallbacks**: If data missing, raise `RuntimeError` to prevent hallucinations
4. **Disk-based caching**: Embeddings persist across restarts
5. **Automated quality checks**: Git hooks + Makefile targets enforce standards
6. **Small files**: ~250 lines max per file for faster linting and clearer diffs

## Next Steps

- [ ] Extract embeddings.py from server.py (lines 639-871)
- [ ] Extract bot.py from server.py (lines 872+)
- [ ] Update all imports after extraction
- [ ] Test with `make check` and manual import test
- [ ] Update Render service name to poe-lastz-v0-8-2
