# Last Z: Survival Shooter Game Analysis Bot

A sophisticated Poe server bot that analyzes Last Z screenshots and provides strategic gameplay advice using dynamic RAG integration with the lastz-mcp service.

## 🎯 Features

### Screenshot Analysis
- **Hero Recognition**: Identifies heroes, levels, and power ratings
- **Building Analysis**: Detects base structures and upgrade levels  
- **Resource Tracking**: Monitors resource amounts and production
- **Strategic Recommendations**: Provides personalized advice based on analysis

### Expert Knowledge Base
- **Hero Strategies**: Tier lists, builds, and team compositions
- **Base Development**: Building priorities and upgrade paths
- **Progression Guide**: Early, mid, and late-game strategies
- **Resource Management**: Efficient allocation and investment advice

### Dynamic RAG Integration
- **Real-time Analysis**: Connects to production MCP service at `https://lastz-mcp.onrender.com`
- **Structured Data Extraction**: Uses advanced image processing and OCR
- **Contextual Advice**: Tailors recommendations to your specific game state

## 🚀 Quick Start

### 1. Set Up Environment
```bash
cd /Users/bradleycoughlin/local_code/poe-server-scratch
pip install -r requirements.txt
```

### 2. Configure Modal (One-time setup)
```bash
modal token new --source poe
```

### 3. Create Poe Bot
1. Go to [poe.com/create_bot](https://poe.com/create_bot)
2. Select "Server bot"
3. Choose a name like "Last Z Expert" or "LastZ Advisor"
4. Save the **Bot Name** and **Access Key**

### 4. Set Environment Variables
Create a `.env` file (copy from `.env.example`):
```bash
POE_ACCESS_KEY=your_access_key_here
POE_BOT_NAME=your_bot_name_here
```

### 5. Deploy
```bash
# For development (live reload):
modal serve lastz_game_bot.py

# For production:
modal deploy lastz_game_bot.py
```

### 6. Connect to Poe
1. Copy the Modal URL from terminal output
2. Paste into your Poe bot's "Server URL" field
3. Test by messaging your bot on Poe

## 💬 How to Use

### Text Queries
Ask questions about Last Z strategy:
- "What are the best heroes for beginners?"
- "How should I prioritize building upgrades?"
- "What's the optimal progression strategy?"

### Screenshot Analysis
1. Upload a screenshot from your Last Z game
2. The bot automatically analyzes the image
3. Receive personalized strategic advice based on your game state

### Example Interactions

**User**: *[uploads hero roster screenshot]*
**Bot**: 
```
🔍 Analyzing your Last Z screenshot...

## 📊 Screenshot Analysis Results

### 🦸 Heroes Detected:
• **William** - Level 45, Power: 125,430
• **Katrina** - Level 38, Power: 98,650
• **Evelyn** - Level 42, Power: 115,220

## 🎯 Strategic Recommendations
• Focus on William - highest power potential
• Consider upgrading Katrina's leadership skills
• Balance your team with a tank hero
```

## 🏗️ Architecture

### Components
- **LastZGameBot**: Main bot class handling Poe interactions
- **MCP Integration**: Connects to lastz-mcp.onrender.com for analysis
- **Strategic Advisor**: Provides context-aware gameplay recommendations
- **Image Processing**: Handles screenshot uploads and analysis

### Data Flow
1. **User Upload**: Screenshot shared via Poe interface
2. **Image Analysis**: Sent to MCP service for processing
3. **Data Extraction**: Heroes, buildings, resources identified
4. **Strategic Analysis**: Recommendations generated based on game state
5. **Response**: Formatted advice delivered to user

## 🔧 Configuration

### Environment Variables
- `POE_ACCESS_KEY`: Your Poe bot access key
- `POE_BOT_NAME`: Your bot's name on Poe
- `MCP_BASE_URL`: MCP service URL (defaults to production service)

### Bot Settings
- **Dependencies**: GPT-4 for advanced reasoning
- **Attachments**: Enabled for screenshot uploads
- **Introduction**: Welcome message explaining capabilities

## 🎮 Supported Analysis Types

### Hero Analysis
- Power levels and potential
- Skill configurations
- Equipment recommendations
- Team composition advice

### Base Analysis  
- Building levels and priorities
- Resource production efficiency
- Defensive structure placement
- Upgrade sequence optimization

### Strategic Planning
- Short-term objectives
- Long-term progression paths
- Resource allocation strategies
- PvP vs PvE focus recommendations

## 📊 Cost Expectations

### Modal Deployment
- **Free Tier**: $30/month credits included
- **Usage-Based**: Pay only when bot processes requests
- **Typical Cost**: $1-5/month for moderate usage
- **Scaling**: Automatic based on demand

### MCP Service
- **Production Service**: Already deployed and operational
- **No Additional Cost**: Integrated service included
- **High Availability**: Production-ready infrastructure

## 🔐 Security & Privacy

### Data Handling
- Screenshots processed in real-time
- No permanent storage of user images
- Analysis results not retained
- Privacy-focused design

### Authentication
- Secure Poe API integration
- Environment variable protection
- Production-ready security practices

## 🛠️ Development

### Local Testing
```bash
# Run locally for development
python lastz_game_bot.py

# Test with curl
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

### Adding Features
- Extend analysis types in `_analyze_screenshot()`
- Add new advice categories in strategic methods
- Integrate additional game systems
- Enhance recommendation algorithms

## 📝 Troubleshooting

### Common Issues
1. **Bot Not Responding**: Check Modal deployment status
2. **Analysis Fails**: Verify MCP service is healthy at `/health`
3. **Credentials Error**: Ensure POE_ACCESS_KEY and POE_BOT_NAME are set
4. **Image Upload Issues**: Confirm attachment permissions enabled

### Debug Commands
```bash
# Check MCP service health
curl https://lastz-mcp.onrender.com/health

# Test Modal deployment
modal logs lastz-game-bot

# Verify requirements
pip check
```

## 🚀 Next Steps

### Phase 1: Enhanced Analysis
- [ ] Advanced hero stat extraction
- [ ] Building optimization recommendations
- [ ] Resource efficiency calculations
- [ ] Battle formation suggestions

### Phase 2: Intelligence Features
- [ ] Progression tracking over time
- [ ] Comparative analysis with optimal builds
- [ ] Predictive upgrade recommendations
- [ ] Alliance strategy integration

### Phase 3: Community Features
- [ ] Multi-user comparison analytics
- [ ] Leaderboard integration
- [ ] Strategy sharing platform
- [ ] Tournament preparation tools

## 📚 References

- **Last Z RAG System**: `/Users/bradleycoughlin/local_code/lastz-rag`
- **MCP Service**: `https://lastz-mcp.onrender.com`
- **Poe Platform**: [creator.poe.com](https://creator.poe.com)
- **Modal Deployment**: [modal.com](https://modal.com)

---

**Ready to dominate Last Z with AI-powered strategic analysis!** 🎮🚀