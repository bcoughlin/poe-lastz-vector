# Last Z Vector RAG Bot

A Poe bot for Last Z: Survival Shooter using vector-based Retrieval Augmented Generation with dynamic data loading from Render disk.

## Quick Links

- 📐 **[ARCHITECTURE.md](ARCHITECTURE.md)** - Project structure, module design, symlink pattern
- 📝 **[notes/](notes/)** - Historical planning documents and development notes

## Key Features

- **Dynamic Knowledge Loading**: Automatically loads data from Render disk
- **Vector Search**: Semantic search with OpenAI embeddings
- **Anti-Hallucination**: Debug footer showing sources + strengthened system prompts
- **Disk-Cached Embeddings**: Persistent across restarts for fast startup
- **Symlink Versioning**: Easy version switching without config changes

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
bash sync_data.sh && python -m uvicorn bot_symlink.server:app --host 0.0.0.0 --port $PORT
```

**Current version**: v0.8.2 via `bot_symlink` → `poe_lastz_v0_8_2/`

**Production URL**: https://poe-lastz-v0-8-1.onrender.com

See [ARCHITECTURE.md](ARCHITECTURE.md) for details on the symlink versioning pattern and how to switch versions.

## Project Structure

```
poe-lastz-vector/
├── bot_symlink/           # → poe_lastz_v0_8_2/ (active version)
├── poe_lastz_v0_8_2/     # Current production code
│   ├── server.py         # Main entry point
│   ├── knowledge_base.py # Data loading
│   ├── logger.py         # Interaction logging
│   └── prompts.py        # System prompts
├── Makefile              # Development commands
└── scripts/              # Setup scripts
```

Full architecture details in [ARCHITECTURE.md](ARCHITECTURE.md).

## Troubleshooting

- **Import errors**: Check `bot_symlink` points to correct version with `ls -la bot_symlink`
- **Linting errors**: Run `make lint-fix` to auto-fix most issues
- **Data loading fails**: Check `sync_data.sh` executed successfully and `/mnt/data` mounted
- **Embeddings cache errors**: Delete `embeddings_cache.pkl` and restart
