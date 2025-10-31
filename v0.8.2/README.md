# Last Z Bot v0.8.2

Current production version with modular structure.

## Structure

```
v0.8.2/
├── bot.py                    # Main entry point (1200 lines - to be refactored)
├── lastz_bot/                # Modular components (WIP)
│   ├── data_collection/      # Interaction logging
│   │   ├── logger.py
│   │   └── __init__.py
│   ├── utils/                # Utilities
│   │   └── prompts.py        # System prompt loading
│   └── __init__.py
└── README.md                 # This file
```

## Features (v0.8.2)

- ✅ Full JSON data delivery for structured content (heroes, buildings, research)
- ✅ Anti-hallucination measures with debug footer
- ✅ Temperature set to 0.6 for balanced responses
- ✅ Disk-based embedding cache
- ✅ GitHub Actions auto-refresh on data changes
- ✅ Admin refresh endpoint with embedding regeneration

## Deployment

Currently deployed to Render as `poe-lastz-v0-8-1` (name will be updated).

**Entry point**: `v0.8.2/bot.py`

**Start command**:
```bash
bash sync_data.sh && python -m uvicorn v0.8.2.bot:app --host 0.0.0.0 --port $PORT
```

## Next Steps

- [ ] Complete modular refactoring (extract knowledge base functions)
- [ ] Update Render deployment to use new structure
- [ ] Rename Render service to poe-lastz-v0-8-2
