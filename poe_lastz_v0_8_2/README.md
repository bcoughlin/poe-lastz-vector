# Last Z Bot v0.8.2

Enhanced knowledge delivery bot with dynamic prompt switching and robust error handling.

## Features

### 🎯 Dynamic Prompt Switching

Switch between different bot personalities on the fly by using `@PROMPT_NAME` syntax in your message:

```
User: "Hey, can you help me @GAMER perspective on this strategy?"
Bot: [Switches to gamer.md prompt and responds]
```

**Available Prompts:**
- `@GAMER` → Enthusiastic Last Z strategy expert (gamer.md)
- `@DESIGNER` → [Add description] (designer.md)
- Add custom prompts by creating `.md` files in `/prompts` directory

**How it works:**
1. User includes `@PROMPT_NAME` in their message
2. Server detects the pattern and loads the corresponding `.md` file
3. Bot responds using the requested prompt for that message
4. Pattern matching is case-insensitive: `@test`, `@TEST`, `@Test` all work

**Alternative syntax if @ doesn't work:**
- `[TEST]` - square brackets
- `{TEST}` - curly braces
- `!TEST` - exclamation mark

### 📁 Prompts Directory

All bot prompts are stored in `poe_lastz_v0_8_2/prompts/`:

```
poe_lastz_v0_8_2/prompts/
├── gamer.md          # Last Z strategy expert persona
├── designer.md       # Design-focused perspective
└── test.md          # Test/experimental prompts (optional)
```

**Adding a new prompt:**
1. Create a new `.md` file in `/prompts` directory
2. Write your prompt content
3. Reference it with `**FILENAME**` (without .md extension)
4. No code changes needed - dynamic discovery handles it!

### 🔒 Error Handling

#### Startup Errors
If critical files are missing at startup, the bot will immediately show:
```
🆘 **Service Error**
I'm experiencing technical difficulties and cannot process your request properly. 
Please contact **support@powra.ai** for assistance.
```

This prevents silent failures and ensures users get proper support contact info.

#### Runtime Errors
Any runtime errors are caught and gracefully handled with the same support message.

**Fail-Fast Strategy:**
- ❌ Missing system prompt → crashes with clear error
- ❌ Missing knowledge base → crashes with clear error  
- ❌ Runtime exception → caught and reported to user

### 🧠 Knowledge Base Integration

The bot searches your knowledge base for every query to prevent hallucinations:
- Embeddings are pre-computed at startup
- Results are limited to top 3 matches
- Bot is instructed to ONLY use knowledge base results
- Falls back gracefully if knowledge not found

## Architecture

### File Structure
```
poe_lastz_v0_8_2/
├── server.py              # FastAPI app & bot class
├── prompts.py            # Prompt loading & switching logic
├── knowledge_base.py     # Knowledge base search
├── logger.py             # Data logging & interaction tracking
├── prompts/              # Prompt files
│   ├── gamer.md
│   ├── designer.md
│   └── test.md
└── README.md            # This file
```

### Key Components

**prompts.py** - Prompt Management
- `find_prompts_directory()` - Locates `/prompts` folder (works from any directory)
- `get_available_prompts()` - Returns dict of all available prompts
- `detect_prompt_request()` - Detects `**PROMPT_NAME**` in user messages
- `load_prompt_by_name()` - Loads specific prompt file
- `load_system_prompt()` - Loads default prompt (first alphabetically)

**server.py** - Bot Server
- `LastZBot` - PoeBot class handling user requests
- `CURRENT_SYSTEM_PROMPT` - Active prompt (switches per request)
- Startup error tracking with `STARTUP_ERROR` global
- Dynamic prompt switching in `get_response()`

## Deployment

### Environment Variables
- `OPENAI_API_KEY` - Required for embeddings
- `POE_ACCESS_KEY` - Optional, for Poe authentication
- `POE_BOT_NAME` - Optional, bot name on Poe

### Render Deployment
- Base image: Python 3.11 (Debian Bullseye)
- Port: 8000
- Health check: `/health` endpoint
- Auto-deploy on git push to main branch

### Data Requirements
Knowledge base data should be:
1. Cloned into `/mnt/data` at startup (Render disk)
2. Discovered and loaded by `knowledge_base.load_knowledge_base()`
3. Embeddings pre-computed on startup

## Usage Examples

### Switching Prompts Mid-Conversation

```
User: "What's the best strategy for building a town hall?"
Bot: [Responds with default gamer perspective]

User: "Can you explain that from a **DESIGNER** perspective?"
Bot: [Switches to designer.md and responds with design focus]

User: "Let me test with **TEST**"
Bot: [Switches to test.md if available, or shows error]
```

### Error Scenarios

**Missing Prompt File:**
```
User: "Help me with **NONEXISTENT**"
Bot: [Logs "Prompt switch failed", continues with current prompt]
```

**Missing System Prompt at Startup:**
```
Logs: "❌ CRITICAL: Failed to load system prompt"
Bot: Shows support contact message to all users
```

## Development

### Testing Prompts
1. Add test prompt to `/prompts/test.md`
2. Send message: "Help me **TEST** this"
3. Check logs for: "🎯 Switched to prompt: test"

### Adding Custom Prompts
1. Create `poe_lastz_v0_8_2/prompts/custom.md`
2. Write prompt content
3. Users can switch with `**CUSTOM**`

### Debugging

**Check available prompts:**
```python
from poe_lastz_v0_8_2.prompts import get_available_prompts
prompts = get_available_prompts()
print(list(prompts.keys()))
```

**Test prompt detection:**
```python
from poe_lastz_v0_8_2.prompts import detect_prompt_request
result = detect_prompt_request("Help me **GAMER** please")
print(result)  # Output: 'gamer'
```

**Load specific prompt:**
```python
from poe_lastz_v0_8_2.prompts import load_prompt_by_name
content = load_prompt_by_name('designer')
```

## Recent Changes

### v0.8.2 Enhancements
- ♻️ Reorganized prompts to `/prompts` directory
- 🎯 Dynamic prompt switching via `**PROMPT_NAME**` syntax
- 🆘 Runtime error handling with support contact message
- 📦 No hardcoded paths - prompts discovered dynamically
- ✅ Fail-fast on missing critical files

## Support

If you encounter issues:
1. Check server logs for error messages
2. Verify all prompt files exist in `/prompts`
3. Ensure `OPENAI_API_KEY` environment variable is set
4. Check `/health` endpoint for startup status
5. Contact support@powra.ai for deployment issues
