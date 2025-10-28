# Render Disk Setup Guide - v0.8.1

## Overview
v0.8.1 uses **Render Disks** to mount the comprehensive Last Z knowledge base from the `lastz-rag` repository. This eliminates hallucinations and provides the bot with accurate game data.

## Architecture

```
poe-lastz-vector (this repo)     lastz-rag (data repo)
├── poe_lastz_v0_8_1.py          ├── data/
├── render.yaml                  │   ├── data_index.md (config)
└── requirements_render.txt      │   ├── heroes/
                                 │   ├── buildings/
                                 │   ├── research/
                                 │   ├── core/ (markdown guides)
                                 │   └── ...
                                 └── kb/ (knowledge base articles)

                 ↓ synced to ↓

         Render Disk: /mnt/data
```

## Render Configuration

### render.yaml
```yaml
disk:
  name: lastz-knowledge-base
  mountPath: /mnt/data
  sizeGB: 1
```

### Data Path Detection (poe_lastz_v0_8_1.py)
```python
data_path_options = [
    "/mnt/data",  # Render Disk mount point (PRODUCTION)
    "../lastz-rag/data",  # Local development fallback
    # ... other fallbacks
]
```

## Initial Setup (One-Time)

### 1. Deploy to Render
```bash
cd /Users/bradleycoughlin/local_code/poe-lastz-vector
git add render.yaml poe_lastz_v0_8_1.py sync_data.sh
git commit -m "Add Render Disk for knowledge base"
git push origin main
```

Render will automatically:
- Create a 1GB persistent disk named `lastz-knowledge-base`
- Mount it at `/mnt/data` in the container
- Run `sync_data.sh` on startup to clone/update lastz-rag repo
- Start the bot with fully loaded knowledge base

**No SSH required!** The `sync_data.sh` script runs automatically on every deployment.

### 2. Verify Deployment
Check Render logs for:
```
🔄 Syncing lastz-rag data to Render Disk...
📥 Cloning data repo for first time...
✅ Data cloned successfully
📚 Loading knowledge base from: /mnt/data/lastz-rag/data
✅ Loaded 150+ total knowledge items
```

## Updating Knowledge Base (Regular Maintenance)

### Option A: Automatic on Redeploy (Recommended)
Every time you deploy (git push), `sync_data.sh` automatically runs and pulls latest data:
```bash
# Just deploy normally
git push origin main

# Render will:
# 1. Run sync_data.sh (pulls latest lastz-rag)
# 2. Start bot with refreshed knowledge
```

### Option B: API Endpoint (No Deploy Needed)
Refresh data without redeploying using the admin endpoint:

```bash
# Set ADMIN_API_KEY in Render dashboard first
curl -X POST "https://lastz-bot-v0-8-1.onrender.com/admin/refresh-data?api_key=YOUR_SECRET_KEY"

# Response:
{
  "status": "success",
  "old_count": 152,
  "new_count": 165,
  "git_output": "Already up to date."
}
```

**Setup ADMIN_API_KEY:**
1. Go to Render Dashboard → lastz-bot-v0-8-1 → Environment
2. Add env var: `ADMIN_API_KEY` = `your-random-secret-key`
3. Save (no redeploy needed)

### Option C: SSH (Fallback)
Only needed if automated methods fail:
```bash
# SSH into Render instance
cd /mnt/data/lastz-rag
git pull origin main

# Then restart service via Render dashboard
```

## Data Structure Requirements

The bot expects this structure in `/mnt/data/lastz-rag/`:

```
lastz-rag/
├── data/
│   ├── data_index.md          # Loading configuration
│   ├── core/                  # Core markdown guides
│   │   ├── early_game.md
│   │   ├── progression.md
│   │   └── ...
│   ├── heroes/                # Hero JSON files
│   │   ├── hero_fiona.json
│   │   ├── hero_brad.json
│   │   └── ... (21+ heroes)
│   ├── buildings/             # Building JSON files
│   ├── research/              # Research JSON files
│   ├── equipment.json
│   ├── troops.json
│   └── ...
└── kb/                        # Knowledge base articles
    ├── hero_strategies/
    ├── building_guides/
    └── ...
```

## Cost Analysis

### Render Disk Pricing
- **1GB Disk**: FREE (included in Starter plan)
- **10GB Disk**: $0.25/GB/month = $2.50/month
- **Current Usage**: ~50MB (data + repo) = FREE tier sufficient

### Comparison
| Solution | Monthly Cost | Notes |
|----------|-------------|-------|
| Modal Volume | $741 (inferred from bill) | Legacy solution |
| Render Disk (1GB) | $0 | Current solution ✅ |
| Render Disk (10GB) | $2.50 | Future expansion |

## Troubleshooting

### Bot Still Hallucinating
**Check logs for:**
```
❌ WARNING: Data directory not found! Using minimal fallback knowledge.
```

**Fix:** Verify data synced correctly:
```bash
# SSH into Render
ls -la /mnt/data/lastz-rag/data/
ls -la /mnt/data/lastz-rag/data/heroes/
```

### Data Not Loading
**Check logs for:**
```
⚠️ data_index.md not found, using legacy loading
```

**Fix:** Ensure `data_index.md` exists:
```bash
cat /mnt/data/lastz-rag/data/data_index.md
```

### Git Pull Fails
**Issue:** SSH key not configured in Render instance

**Fix:** Use HTTPS with token:
```bash
cd /mnt/data/lastz-rag
git remote set-url origin https://YOUR_TOKEN@github.com/bcoughlin/lastz-rag.git
git pull origin main
```

## Testing

### Verify Knowledge Base Loaded
Test with previously hallucinating query:
```
User: "what weapons are in the game?"

BEFORE (hallucinating):
"Last Z features ARs, snipers, LMGs..." ❌

AFTER (correct):
"Last Z doesn't use traditional weapon categories. Heroes use equipped weapons 
that provide stat bonuses..." ✅
```

### Check Hero Data
```
User: "tell me about Fiona"

Expected: Accurate stats from hero_fiona.json
```

### Verify Embedding Search
```
User: "best early game heroes"

Expected: Search across 150+ knowledge items, return relevant hero data
```

## Next Steps

1. ✅ Deploy render.yaml with disk configuration
2. ✅ Update data_path_options in poe_lastz_v0_8_1.py
3. ⏳ SSH into Render and clone lastz-rag to /mnt/data
4. ⏳ Verify logs show "Loaded 150+ total knowledge items"
5. ⏳ Test with "weapons" query (should not hallucinate)
6. ⏳ Set up git pull workflow for regular updates

## Reference Links

- [Render Disks Documentation](https://render.com/docs/disks)
- [lastz-rag Data Repository](https://github.com/bcoughlin/lastz-rag)
- [Render SSH Access](https://render.com/docs/ssh)
