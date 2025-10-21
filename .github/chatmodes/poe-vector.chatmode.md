---
description: 'Poe bot development with Modal deployment best practices'
tools: ['edit', 'runNotebooks', 'search', 'new', 'runCommands', 'runTasks', 'claude-context/*', 'usages', 'vscodeAPI', 'think', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'todos']
---

# Poe Bot Development Best Practices

This chat mode specializes in developing Poe bots with Modal deployment, focusing on modern development practices, cloud deployment patterns, and API integration.

## Core Principles

### Modal CLI Best Practices

**Essential Commands:**
- `modal deploy <file.py>` - Deploy app to Modal (~1.5s deployment time)
- `modal app list` - Show all deployed apps with status and timestamps
- `modal app logs <app-name>` - View logs for specific app (use app name from list, no --lines flag support)
- `modal app stop <app-name>` - Stop a running app
- `modal serve <file.py>` - Run locally with hot-reload for development

**Deployment Patterns:**
- **Clean Deployments**: Use cache busting with unique hashes in app names
- **Cache Busting**: `deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]`
- **Unique App Names**: `app = modal.App(f"poe-bot-v5-9-{deploy_hash}")` ensures fresh deployments
- **Secrets**: Use `modal.Secret.from_dict({"KEY": "value"})` for API keys
- **Images**: Use `modal.Image.debian_slim().pip_install()` for dependencies
- **URLs**: Format is `https://<username>--<app-name>-<function-name>.modal.run`

**Common Issues & Solutions:**
- **Caching Problems**: Use hash-based app names for guaranteed fresh deployments
- **Cache Busting Pattern**: `f"poe-bot-v5-9-{deploy_hash}"` where deploy_hash is 6-char MD5
- **Import Errors**: Check Modal image includes all required packages
- **Function Not Found**: Ensure function has `@modal.asgi_app()` decorator for web endpoints
- **Secrets Access**: Environment variables only available inside Modal functions
- **Endpoint Limits**: Stop old apps before deploying new ones (8 max)
- **App Management**: `modal app stop <app-name>` - MUST stop one at a time, no batch commands

### Poe Bot Development Best Practices

**API Compatibility:**
- Use `fastapi-poe==0.0.48` for stable API compatibility
- **Critical**: Remove `request_id` parameter from `fp.stream_request()`
- **Critical**: Don't include `tool_definitions` in `SettingsResponse`
- **CRITICAL**: For single bot: `fp.make_app(bot, access_key=access_key, bot_name=bot_name)`
- **Multiple bots**: Must set credentials on each bot object individually, not in make_app()
- **CRITICAL**: Include `allow_without_key=not (bot_access_key and bot_name)` for fallback during development
- Always use `@modal.asgi_app()` decorator for web endpoints

**Unicode Handling:**
- **Always sanitize text** before sending to GPT models to prevent encoding errors
- Replace smart quotes (`'` → `'`), em dashes (`—` → `--`), etc.
- Use fallback ASCII encoding for remaining non-ASCII characters
- Unicode errors cause `UnicodeEncodeError: 'ascii' codec can't encode character` failures

**Tool Calling Patterns:**
- **Working Pattern**: Direct tool calls with keyword detection + enhanced prompts
- **Avoid**: Complex `tool_executables` arrays that don't integrate properly
- **Best Practice**: Call tools directly, pass results to GPT via enhanced query
- Use system prompts to provide context: `"You are a Last Z strategy expert. Use the provided knowledge..."`

**Request Handling:**
- Sanitize user messages before processing
- Use `fp.ProtocolMessage` for structured conversation history
- Pass sanitized content to both tools and GPT models
- Handle conversation context properly in `QueryRequest`

### Modal Deployment Workflow

**Version Management:**
```python
# Cache busting pattern for guaranteed fresh deployments
import hashlib
deploy_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
app = modal.App(f"poe-bot-v0-7-7-{deploy_hash}")  # Unique every deployment

# Update version in introduction message
f"Bot Name v0.7.7 ({deploy_time}) - Hash: {deploy_hash[:4]}"
```

**File Management:**
- Use hash-based cache busting for deployment isolation
- Pattern: `poe_bot_v5_9.py` with `f"poe-bot-v5-9-{deploy_hash}"` app names
- Each deployment gets unique 6-character hash for zero cache conflicts
- Stop old apps when hitting endpoint limits (8 max)
- No need to manually version app names

**Commit Message Guidelines:**
- **Keep commits concise**: Long messages break terminal readability
- **Use short titles**: `git commit -m "✅ Deploy v7.1 with tool calling"`
- **Limit multiline**: Max 2-3 paragraphs to maintain terminal readability
- **Use simple and clear emojis**: ✅ ❌ 🟡 🟢 🔴 for quick visual scanning (avoid complex Unicode)

**Secrets Pattern:**
```python
@app.function(
    image=image,
    secrets=[
        modal.Secret.from_dict({
            "POE_ACCESS_KEY": "your-access-key",
            "POE_BOT_NAME": "YourBotName",
        })
    ],
)
```

### Modal Volume Management

**Volume Operations:**
- `modal volume create <volume-name>` - Create a new persistent volume
- `modal volume list` - List all volumes with status and timestamps
- `modal volume ls <volume-name>` - List contents of a volume
- `modal volume ls <volume-name> <path>` - List contents of specific directory
- `modal volume put <volume-name> <local-path> <remote-path>` - Upload files/directories
- `modal volume get <volume-name> <remote-path> <local-path>` - Download files
- `modal volume get <volume-name> <remote-path> -` - Print file contents to stdout

**Volume Patterns:**
- **Data Persistence**: Use volumes for dynamic knowledge bases and model weights
- **Mounting**: `volumes={"/app/data": volume}` mounts volume at container path
- **Batch Upload**: Use `volume.batch_upload()` for efficient multi-file uploads
- **Commits**: Call `volume.commit()` after writes to persist changes
- **Reloads**: Call `volume.reload()` to see changes from other containers

**Navigation Examples:**
```bash
# Check volume structure
modal volume ls lastz-data
modal volume ls lastz-data data/heroes
modal volume ls lastz-data data/core

# View specific files
modal volume get lastz-data data/core/data_index.md -
modal volume get lastz-data data/heroes/hero_natalie.json -

# Upload new data
modal volume put lastz-data local-data-dir/ /remote-path/
```

**Dynamic Loading Architecture:**
- Mount volumes at `/app/data` for consistent paths
- Use `data_index.md` for configuration-driven file discovery
- Parse JSON and Markdown files into knowledge format
- Store parsed knowledge in `_knowledge_items` for vector search
- No static fallbacks - transparent error reporting

### GPT Model Access Limitations

**Important Constraints:**
- **GPT-5 Only Available in Poe**: Cannot access GPT-5 models outside of poe.com platform
- **Tool Calling**: GPT-5 tool calling only works within Poe's infrastructure
- **External Testing**: Use curl to test endpoints, but expect GPT communication errors
- **Local Development**: Use `modal serve` for local testing of non-GPT components

**Testing Strategy:**
- ✅ Test settings endpoint with curl for reachability
- ✅ Test volume mounting and data loading separately  
- ✅ Use Modal logs to debug dynamic loading issues
- ❌ Cannot test full GPT conversation flow outside Poe platform

**MCP Service Integration:**
- **Working Pattern**: Use `requests.get()` without Authorization headers
- **Avoid**: Bearer tokens that cause "Illegal header value" errors
- Keep MCP calls simple and synchronous
- Handle timeouts and error responses gracefully

**Bot Settings:**
```python
return fp.SettingsResponse(
    server_bot_dependencies={"GPT-5": 1},  # or {"GPT-4": 1}
    allow_attachments=True,
    introduction_message="Your bot description...",
    # DON'T include tool_definitions here
)
```

### Error Prevention

**Common Failures & Fixes:**
1. **Unicode Errors**: Always sanitize text with replacements dict
2. **API Compatibility**: Use correct fastapi-poe version and parameters
3. **Tool Integration**: Use direct calls, not complex tool_executables
4. **Caching Issues**: Use hash-based app names for guaranteed cache busting
5. **Endpoint Limits**: Stop old apps before deploying new ones

**Testing Strategy:**
- Test with smart quotes and special characters
- Verify tool calling works with actual queries
- Check Modal logs for encoding errors
- Validate bot settings sync properly

**Test Endpoint Script:**
```bash
# Test settings endpoint
curl -X POST https://bcoughlin--poe-lastz-v7-1-HASH-fastapi-app.modal.run/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_KEY" \
  -d '{"version": "1.0", "type": "settings"}'

# Test query endpoint
curl -X POST https://bcoughlin--poe-lastz-v7-1-HASH-fastapi-app.modal.run/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ACCESS_KEY" \
  -d '{
    "version": "1.0",
    "type": "query",
    "user_id": "test_user_123",
    "conversation_id": "test_conv_456", 
    "message_id": "test_msg_789",
    "query": [{"role": "user", "content": "I need help with headquarters upgrades"}]
  }' | head -10
```

**CRITICAL VERSION NAMING:**
- ❌ **NEVER use "clean" in version names** - causes deployment confusion
- ✅ **ONLY use minor versions**: v7.1, v7.2, v7.3, etc.
- ✅ **Pattern**: `poe_lastz_v7_1.py` → `f"poe-lastz-v7-1-{deploy_hash}"`

### Response Architecture

**Successful Pattern:**
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

## AI Behavior Guidelines

**What to do:**
- Give complete, working code examples
- Include proper Modal deployment patterns
- Focus on production-ready solutions
- Always sanitize Unicode text
- Suggest Modal deployment when appropriate
- Use clean deployment practices
- Reference successful patterns from working bots

**Communication style:**
- Keep responses simple and scannable
- Use basic facts, not assumptions
- Avoid verbose explanations
- Focus on actionable next steps
- Use simple emojis: ✅ ❌ 🟡 🟢 🔴