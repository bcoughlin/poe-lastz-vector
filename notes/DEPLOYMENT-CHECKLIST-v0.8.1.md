# Deployment Checklist - v0.8.1 with Render Disk

## Pre-Deployment (Local)

- [x] ✅ Updated `render.yaml` with Render Disk configuration
- [x] ✅ Updated data_path_options in `poe_lastz_v0_8_1.py`
- [x] ✅ Created `sync_data.sh` for automatic data syncing
- [x] ✅ Added `/admin/refresh-data` endpoint for manual refresh
- [x] ✅ Created RENDER-DISK-SETUP.md guide
- [ ] ⏳ Commit and push changes

## Commands to Deploy

```bash
cd /Users/bradleycoughlin/local_code/poe-lastz-vector

# Stage changes
git add render.yaml poe_lastz_v0_8_1.py sync_data.sh notes/

# Commit with descriptive message
git commit -m "v0.8.1: Automated Render Disk sync for knowledge base

- Add sync_data.sh script to auto-clone/update lastz-rag on startup
- Add /admin/refresh-data endpoint for manual updates without redeploy
- Configure 1GB Render Disk at /mnt/data
- Update data_path_options to prioritize /mnt/data/lastz-rag/data
- Fixes hallucination issue by loading 150+ knowledge items
- NO SSH REQUIRED - fully automated deployment"

# Push to trigger deployment
git push origin main
```

## Post-Deployment (Render Dashboard)

### 1. Wait for Deployment
- [ ] ⏳ Check Render Dashboard for successful build
- [ ] ⏳ Verify disk `lastz-knowledge-base` created and mounted
- [ ] ⏳ Check logs for automated data sync

### 2. Verify Automated Sync (No SSH Needed!)
Check logs should show:
```
🔄 Syncing lastz-rag data to Render Disk...
📥 Cloning data repo for first time...
✅ Data cloned successfully
📚 Loading knowledge base from: /mnt/data/lastz-rag/data
✅ Loaded 150+ total knowledge items
```

### 3. (Optional) Set Up Admin API Key
For manual data refresh without redeploying:
- [ ] ⏳ Add `ADMIN_API_KEY` env var in Render Dashboard
- [ ] ⏳ Test with: `curl -X POST "https://lastz-bot-v0-8-1.onrender.com/admin/refresh-data?api_key=YOUR_KEY"`

### 4. Test Functionality
- [ ] ⏳ Test "weapons" query (should NOT hallucinate ARs/LMGs)
- [ ] ⏳ Test "tell me about Fiona" (should load from hero_fiona.json)
- [ ] ⏳ Test "best early game heroes" (embedding search across knowledge base)

## Expected Log Output (Success)

```
� Syncing lastz-rag data to Render Disk...
📥 Cloning data repo for first time...
Cloning into 'lastz-rag'...
✅ Data cloned successfully
📊 Data structure:
total 128
drwxr-xr-x  heroes/
drwxr-xr-x  buildings/
drwxr-xr-x  research/
✅ Data sync complete!

�🚀 Starting Last Z Assistant v0.8.1 (Render Production)
📊 Data Storage: /tmp/lastz_data
📚 Loading knowledge base...
✅ Found data directory: /mnt/data/lastz-rag/data
📚 Loading knowledge base from: /mnt/data/lastz-rag/data
📋 Parsed data_index.md configuration
✅ Loaded core guide: Early Game Progression
✅ Loaded core guide: Hero Basics
✅ Loaded hero: Fiona
✅ Loaded hero: Brad
✅ Loaded hero: Ash
... (20+ heroes)
✅ Loaded building: Headquarters
✅ Loaded building: Training Ground
... (10+ buildings)
✅ Loaded research category: Military
✅ Loaded research category: Development
... (5+ categories)
✅ Loaded 150+ total knowledge items
🔍 Initialized OpenAI embeddings with 150+ documents
✅ Bot initialized successfully
```

## Troubleshooting

### If logs show "Data directory not found"
Check that `sync_data.sh` ran successfully. Look for:
```
🔄 Syncing lastz-rag data to Render Disk...
```

If missing, the script might have failed. Check:
1. Render Disk mounted at `/mnt/data`
2. Script has execute permissions (`chmod +x sync_data.sh`)
3. Git is available in Render environment

### If sync_data.sh fails with "command not found: git"
Git is included in Render Python environments by default. If missing, update `buildCommand`:
```yaml
buildCommand: apt-get update && apt-get install -y git && pip install -r requirements_render.txt
```

### If still hallucinating after deployment
1. Check logs for "Loaded X total knowledge items" (should be 150+)
2. Verify data sync completed: look for "✅ Data sync complete!"
3. Test `/health` endpoint: `curl https://lastz-bot-v0-8-1.onrender.com/health`
   - Should show: `"knowledge_items": 150+`

### Manual data refresh not working
Test the admin endpoint:
```bash
curl -X POST "https://lastz-bot-v0-8-1.onrender.com/admin/refresh-data?api_key=test"

# Should return: {"error": "Unauthorized"} (expected without valid key)
```

Set `ADMIN_API_KEY` in Render Dashboard environment variables.

## Cost Verification

Before: Modal $741/month
After: Render $7/month + Disk $0 = **$7/month total**

**Savings: 99.1%** 🎉

## Success Criteria

✅ Deployment completes without errors
✅ Disk mounted at /mnt/data with 1GB capacity
✅ Data loaded: 150+ knowledge items
✅ No hallucination on "weapons" query
✅ Accurate responses for hero/building queries
✅ Cost: $7/month total
