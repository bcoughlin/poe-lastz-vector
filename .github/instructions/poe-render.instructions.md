---
applyTo: '**'
---

# Poe Bot Render Deployment - Critical Patterns

## Code Search Requirements
- **ALWAYS use claude-context search tools** for code exploration
- ❌ NEVER use grep, find, or other shell commands for searching code
- ✅ Use `mcp_claude-contex_search_code` for finding functions, patterns, code

## Render Deployment Patterns

### Render Disk Integration
- **Disks are ONLY accessible at runtime, NOT during build**
- ❌ Cannot access `/mnt/data` in `buildCommand` or pre-deploy commands
- ✅ Sync external data repos in `startCommand` before app starts
- ✅ Load knowledge bases in FastAPI `@app.on_event("startup")` handler

### Environment Variables
- **Must select "Save, rebuild, and deploy"** when adding env vars
- "Save only" won't make vars available until next deploy
- Private repo cloning requires `GITHUB_TOKEN` with `repo` scope

### Data Loading Pattern
```python
# ❌ WRONG - loads at import (before disk mounted)
knowledge_items = []
load_knowledge_base()  # module level

# ✅ CORRECT - loads after disk mounted
@app.on_event("startup")
async def startup_event():
    load_knowledge_base()
```

### Deployment Order
1. Build: Install deps only
2. Start: `bash sync_data.sh && python -m uvicorn app:app`
3. Sync script: Clone/pull data from external repo to `/mnt/data`
4. App starts: Disk accessible, data ready
5. Startup event: Load knowledge base into memory

### Error Handling
- **Fail fast, no silent fallbacks** - if data missing, raise `RuntimeError` to prevent hallucinations
- Deployment should fail loudly if knowledge base unavailable

## Poe Bot Development Best Practices

### API Compatibility
- Use `fastapi-poe==0.0.48` for stable API compatibility
- **Critical**: Remove `request_id` parameter from `fp.stream_request()`
- **Critical**: Don't include `tool_definitions` in `SettingsResponse`
- **Critical**: For single bot: `fp.make_app(bot, access_key=access_key, bot_name=bot_name)`
- Include `allow_without_key=not (bot_access_key and bot_name)` for fallback during development

### Unicode Handling
- **Always sanitize text** before sending to GPT models to prevent encoding errors
- Replace smart quotes (`'` → `'`), em dashes (`—` → `--`), etc.
- Use fallback ASCII encoding for remaining non-ASCII characters

### Tool Calling Patterns
- **Working Pattern**: Direct tool calls with keyword detection + enhanced prompts
- **Avoid**: Complex `tool_executables` arrays that don't integrate properly
- Use system prompts to provide context: `"You are a Last Z strategy expert..."`

### Request Handling
- Sanitize user messages before processing
- Use `fp.ProtocolMessage` for structured conversation history
- Pass sanitized content to both tools and GPT models

### Git & Development Workflow
- **Keep commits concise**: Long messages break terminal readability
- **Use short titles**: `git commit -m "✅ Deploy v7.1 with tool calling"`
- **Use simple emojis**: ✅ ❌ 🟡 🟢 🔴 for quick visual scanning

### Bot Settings
```python
return fp.SettingsResponse(
    server_bot_dependencies={"GPT-5": 1},  # or {"GPT-4": 1}
    allow_attachments=True,
    introduction_message="Your bot description...",
    # DON'T include tool_definitions here
)
```

### Response Architecture
```python
# 1. Sanitize input
sanitized_message = self.sanitize_text(user_message)

# 2. Detect keywords and call tools
if "headquarters" in sanitized_message.lower():
    knowledge = self.get_knowledge("headquarters")
    
# 3. Create enhanced query with context
enhanced_query = [
    fp.ProtocolMessage(role="system", content="Expert context..."),
    fp.ProtocolMessage(role="user", content=sanitized_message),
    fp.ProtocolMessage(role="assistant", content=f"Knowledge: {knowledge}")
]

# 4. Stream from GPT with context
async for msg in fp.stream_request(sanitized_request, "GPT-5", sanitized_request):
    yield msg
```

### Error Prevention
1. **Unicode Errors**: Always sanitize text with replacements dict
2. **API Compatibility**: Use correct fastapi-poe version and parameters
3. **Tool Integration**: Use direct calls, not complex tool_executables
4. **Import Issues**: Use module imports (knowledge_base.knowledge_items) not direct imports

## AI Behavior Guidelines
- Give complete, working code examples
- Focus on production-ready solutions
- Always sanitize Unicode text
- Keep responses simple and scannable
- Use basic facts, not assumptions
- Focus on actionable next steps