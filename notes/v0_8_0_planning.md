# Last Z Bot v0.8.0 Planning - User Data Collection

## Goal
Collect images and questions from users of the bot to improve knowledge base and understand user needs better.

## Current State (v0.7.9)
- ✅ Bot personality optimized with natural enthusiasm
- ✅ Anti-hallucination guardrails working
- ✅ Real hero names enforced via denylist
- ✅ GPT-5-Chat model with temperature 0.9
- ✅ Modal deployment with prompts mounting
- 🎯 **Current URL**: https://bcoughlin--poe-lastz-v0-7-9-173c4d-fastapi-app.modal.run

## v0.8.0 Feature: User Data Collection

### What to Collect
1. **User Images**: Screenshots uploaded for analysis
2. **User Questions**: Text queries and conversation context
3. **Bot Responses**: Our responses for quality analysis
4. **Interaction Metadata**: Timestamps, user IDs, conversation flows

### Technical Approach Options

#### Option A: Modal Volume Storage
- Store collected data in Modal persistent volumes
- Pros: Integrated with current infrastructure, persistent
- Cons: Need to manage volume storage, potential costs

#### Option B: External Database/Storage
- Send data to external service (S3, Supabase, etc.)
- Pros: Dedicated storage, easier analytics
- Cons: Additional infrastructure, API calls

#### Option C: Local File Export
- Batch export data periodically for analysis
- Pros: Simple implementation, no external deps
- Cons: Manual process, data could be lost

### Privacy Considerations
- ❓ User consent for data collection *(address later)*
- ❓ Anonymization of user IDs *(address later)*
- ❓ Image privacy (game screenshots should be OK) *(address later)*
- ❓ Data retention policies *(address later)*
- **Note**: Focus on technical feasibility first, privacy implementation comes later

### Implementation Questions
1. **When to collect**: Every interaction or selective sampling?
2. **Storage format**: JSON logs, structured database, or file system?
3. **Access method**: How to retrieve and analyze collected data?
4. **User notification**: Should users know their data is being collected?

### Use Cases for Collected Data
- **Knowledge Gap Analysis**: What questions can't we answer well?
- **Image Analysis Improvement**: Common screenshot types and analysis needs
- **User Behavior Patterns**: Most common query types and user flows
- **Bot Response Quality**: Identify responses that need improvement
- **Knowledge Base Expansion**: New heroes, features, or strategies to document

### Next Steps
1. **✅ Design data collection schema** - Created `create_interaction_log()` function
2. **✅ POC Implementation** - Created `poe_lastz_v0_8_0_poc.py` with console logging
3. **🔄 Test POC deployment** - Deploy and test what data we can actually capture
4. **Choose storage approach** (Modal Volume vs external) - Based on POC results
5. **Implement persistent storage** - Once POC proves data collection works
6. Create data analysis workflow
7. Add privacy considerations and user consent *(later phase)*

### POC Implementation Details
- **File**: `poe_lastz_v0_8_0_poc.py`
- **Data Schema**: JSON structure with user_id, conversation_id, messages, images, tool_calls, response_time
- **Logging Method**: Console output for initial testing (will show in Modal logs)
- **Data Captured**: User messages, image count, bot responses, tool usage, response times
- **Testing Approach**: Deploy POC and monitor Modal logs to see what data we can collect

### Success Metrics
- Number of interactions collected per day
- Quality insights gained from user questions
- Knowledge base improvements identified
- Bot response optimization opportunities

---

## Technical Notes
- Current bot uses FastAPI-Poe framework
- Modal deployment with persistent volumes available
- Vector embeddings for knowledge search working well
- Image analysis capabilities already implemented