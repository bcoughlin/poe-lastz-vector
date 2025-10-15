# Multi-Bot Environment Configuration

This setup supports multiple Poe bots with discrete access keys and configurations.

## Environment Variables (.env file)

```bash
# Last Z Game Bot - Advanced screenshot analysis and strategic advice
POE_ACCESS_KEY_LASTZ=your_lastz_bot_key_here
POE_BOT_NAME_LASTZ=LastZGameBot

# Echo Bot - Simple echo functionality for testing
POE_ACCESS_KEY_ECHO=your_echo_bot_key_here
POE_BOT_NAME_ECHO=EchoBot

# Default credentials (fallback if specific ones not set)
POE_ACCESS_KEY=your_default_key_here
POE_BOT_NAME=DefaultBot
```

## Bot Configuration

Each bot now uses its specific environment variables with fallback to defaults:

- **Last Z Bot** (`lastz_game_bot.py`): Uses `POE_ACCESS_KEY_LASTZ` → `POE_ACCESS_KEY`
- **Echo Bot** (`echobot.py`): Uses `POE_ACCESS_KEY_ECHO` → `POE_ACCESS_KEY`

## Deployment Options

### Option 1: Individual Deployment
```bash
# Deploy Last Z bot
python deploy.py lastz

# Deploy Echo bot  
python deploy.py echo
```

### Option 2: Batch Deployment
```bash
# Deploy both bots
python deploy.py both
```

### Option 3: Manual Modal Deployment
```bash
# Deploy specific bot files
modal deploy lastz_game_bot.py
modal deploy echobot.py
```

## Current Deployment Status

- **Last Z Bot**: `https://bcoughlin--lastz-game-bot-serve.modal.run`
- **Echo Bot**: `https://bcoughlin--poe-echo-bot-serve.modal.run`

## Access Key Management

1. **Get your access keys** from Poe Creator Dashboard
2. **Update .env file** with your specific bot keys
3. **Deploy using script** or manual Modal commands
4. **Register bots** in Poe platform with deployment URLs

## Security Notes

- Keep `.env` file out of version control (already in `.gitignore`)
- Each bot should have its own unique access key
- Use descriptive bot names for easy identification
- Test deployment without keys first, then add authentication