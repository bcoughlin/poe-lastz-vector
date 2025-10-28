---
applyTo: '**'
---

# Poe Bot Render Deployment - Critical Patterns

## Render Disk Integration
- **Disks are ONLY accessible at runtime, NOT during build** ([docs](https://render.com/docs/disks#disk-limitations-and-considerations))
- ❌ Cannot access `/mnt/data` in `buildCommand` or pre-deploy commands
- ✅ Sync external data repos in `startCommand` before app starts
- ✅ Load knowledge bases in FastAPI `@app.on_event("startup")` handler, not at module import time

## Environment Variables
- **Must select "Save, rebuild, and deploy"** when adding env vars ([docs](https://render.com/docs/configure-environment-variables))
- "Save only" won't make vars available until next deploy
- Private repo cloning requires `GITHUB_TOKEN` with `repo` scope
- Blueprint env vars with `sync: false` must be set manually in Dashboard

## Data Loading Pattern
```python
# ❌ WRONG - loads at import (before disk mounted)
knowledge_items = []
load_knowledge_base()  # module level

# ✅ CORRECT - loads after disk mounted
@app.on_event("startup")
async def startup_event():
    load_knowledge_base()
```

## Deployment Order
1. Build: Install deps only
2. Start: `bash sync_data.sh && python -m uvicorn app:app`
3. Sync script: Clone/pull data from external repo to `/mnt/data`
4. App starts: Disk accessible, data ready
5. Startup event: Load knowledge base into memory

## Error Handling
- **Fail fast, no silent fallbacks** - if data missing, raise `RuntimeError` to prevent hallucinations
- Deployment should fail loudly if knowledge base unavailable

## Cost Optimization
- Render Starter ($7/mo) + 1GB Disk (FREE) = $7/mo total
- vs Modal ($741/mo) = 99.1% savings