# Last Z Bot v0.8.2

Current production version with modular structure.

## Structure

```
v0.8.2/
├── poe_lastz_v0_8_2.py       # Main bot (1200 lines - production)
├── data_collection/          # Interaction logging utilities
│   ├── logger.py
│   └── __init__.py
├── utils/                    # Utilities
│   └── prompts.py            # System prompt loading
├── knowledge/                # Reserved for knowledge base modules (future)
├── __init__.py               # Package init
└── README.md                 # This file
```

## Features (v0.8.2)

- ✅ Full JSON data delivery for structured content (heroes, buildings, research)
- ✅ Anti-hallucination measures with debug footer showing sources
- ✅ Temperature set to 0.6 for balanced responses
- ✅ Disk-based embedding cache (persistent across restarts)
- ✅ GitHub Actions auto-refresh on data changes
- ✅ Admin refresh endpoint with embedding regeneration

## Deployment

Currently deployed to Render as `poe-lastz-v0-8-1` service.

**Entry point**: `v0.8.2/poe_lastz_v0_8_2.py`

**Start command**:
```bash
bash sync_data.sh && python -m uvicorn v0.8.2.poe_lastz_v0_8_2:app --host 0.0.0.0 --port $PORT
```

## Production URL

https://poe-lastz-v0-8-1.onrender.com

## Next Steps

- [ ] Extract knowledge base loading into knowledge/ module
- [ ] Extract search functions into knowledge/ module
- [ ] Update Render service name to poe-lastz-v0-8-2

