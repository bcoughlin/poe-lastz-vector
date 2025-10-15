# Last Z Vector RAG Bot

A Poe bot for Last Z: Survival Shooter using vector-based Retrieval Augmented Generation with dynamic data loading from Modal volumes.

## Purpose
This project implements vector embeddings and semantic search for game knowledge retrieval, with dynamic data loading from the lastz-rag repository.

## Key Features
- **Dynamic Knowledge Loading**: Automatically loads data from Modal volumes
- **Vector Search**: Semantic search with sentence-transformers
- **Tool-Based Architecture**: GPT-5 tool calling for intelligent interactions
- **No Static Fallbacks**: Pure dynamic loading to verify system integrity

## Setup & Deployment

### 1. Data Volume Setup (CRITICAL)
The bot requires a Modal volume with lastz-rag data. **This must be done before deployment:**

```bash
# Upload lastz-rag data to Modal volume
cd /Users/bradleycoughlin/local_code
modal volume put lastz-data lastz-rag/data /
```

**Note**: If you get "already exists" error, the data is already uploaded. This is expected after first setup.

### 2. Deploy Bot
```bash
cd poe-lastz-vector
modal deploy poe_lastz_v7.py
```

### 3. Volume Management
```bash
# List volume contents
modal volume ls lastz-data

# Check volume status
modal volume list
```

## Architecture
- **Modal Volumes**: Dynamic data storage and loading
- **Index-Driven**: Uses `data_index.md` for automatic file discovery
- **Hybrid Loading**: Core static files + dynamic JSON/markdown directories
- **Vector Search**: sentence-transformers 'all-MiniLM-L6-v2' model
- **No Fallbacks**: Returns clear error messages if dynamic loading fails

## Data Structure
```
/app/data/
├── core/
│   ├── data_index.md      # Loading configuration
│   ├── game_fundamentals.md
│   └── terminology.md
├── heroes/                # Dynamic JSON files
├── buildings/             # Dynamic JSON files
└── research/              # Dynamic markdown files
```

## Troubleshooting
- **"No knowledge available"**: Volume data not uploaded or mount failed
- **"Dynamic loading failed"**: Check Modal volume status and file permissions
- **Vector search errors**: Logs will show specific sentence-transformers issues

## Status
✅ Working dynamic data loading from Modal volumes
✅ Vector search with semantic understanding
✅ Tool calling with GPT-5 integration
✅ Pure dynamic architecture (no static fallbacks)
