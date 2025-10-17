# LastZ Bot v0.7.8 - Image Analysis Integration Planning

**Target Release**: v0.7.8 Beta  
**Focus**: Multi-modal capabilities (Text + Image Analysis)  
**Status**: 📋 Planning Phase

---

## 🖼️ **Core Image Capabilities from Poe API**

### **Built-in Image Support:**
- ✅ `allow_attachments=True` - Enable file uploads
- ✅ `enable_image_comprehension=True` - Automatic image analysis by Poe
- ✅ `should_insert_attachment_messages=True` - Auto-parse image content

### **Image Data Access:**
- **Parsed Content**: `ProtocolMessage.attachments[].parsed_content` - Poe's AI description
- **Raw Image URL**: `attachments[].url` - Direct access for custom analysis
- **Metadata**: `attachments[].content_type`, `attachments[].name`

---

## 🏗️ **v0.7.8 Architecture Plan**

### **1. Settings Updates**
```python
async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
    return fp.SettingsResponse(
        server_bot_dependencies={"GPT-5": 1},
        allow_attachments=True,           # ✅ Enable image uploads
        enable_image_comprehension=True,  # ✅ Auto image analysis
        introduction_message=f"Last Z Assistant v0.7.8 ({deploy_time}) - Hash: {deploy_hash[:4]}\n\n🧠 VECTOR EMBEDDINGS + 🖼️ IMAGE ANALYSIS\n\n✅ Multi-modal LastZ assistant:\n• Upload screenshots for visual analysis\n• Hero/building/equipment identification\n• Strategic advice from game images\n• Combined text + visual search\n\n🎯 Try: Upload your base screenshot + ask 'What should I upgrade next?'"
    )
```

### **2. New Image Analysis Tools**

```python
def analyze_lastz_screenshot(image_description: str, user_query: str) -> str:
    """
    Analyze LastZ game screenshots for strategic advice.
    
    Args:
        image_description: Poe's automated image analysis
        user_query: User's question about the image
    
    Returns:
        Strategic analysis combining visual and knowledge base data
    """
    # Combine image analysis with knowledge base search
    # Identify game elements and provide contextual advice

def identify_game_elements(image_description: str) -> str:
    """
    Identify specific LastZ game elements in screenshots.
    
    Args:
        image_description: Poe's automated image analysis
    
    Returns:
        Structured identification of heroes, buildings, equipment
    """
    # Parse image description for game-specific elements
    # Cross-reference with knowledge base
```

### **3. Enhanced Response Flow**

```python
async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
    """Enhanced response with image + text analysis"""
    
    # Check for image attachments
    has_images = any(msg.attachments for msg in request.query if msg.attachments)
    
    if has_images:
        # Process images + text query
        # Combine visual analysis with knowledge search
        # Provide comprehensive strategic advice
    else:
        # Standard text-only vector search (existing v0.7.7 flow)
```

---

## 🎯 **LastZ-Specific Image Features**

### **Visual Recognition Capabilities:**
- 🏰 **Base Screenshots**: Identify buildings, levels, upgrade priorities
- 👥 **Hero Roster**: Recognize heroes, suggest team compositions  
- ⚔️ **Battle Formations**: Analyze deployment strategies
- 📊 **Resource Screens**: Optimize resource allocation
- 🗺️ **Map Views**: Strategic positioning advice

### **Integration with Existing Knowledge:**
- **Cross-Reference**: Match visual elements with knowledge base
- **Contextual Advice**: Combine image analysis with game guides
- **Similarity Search**: Find related strategies based on visual state

---

## ⚙️ **Technical Implementation**

### **Requirements Updates:**
```python
REQUIREMENTS = [
    "fastapi-poe", "numpy", "scikit-learn", 
    "sentence-transformers", "torch",
    "requests", "pillow"  # For additional image processing if needed
]
```

### **Modal Configuration (unchanged):**
- **CPU**: 4 vCPUs for image + vector processing
- **Memory**: 8GB RAM for embeddings + image analysis
- **Timeout**: 5 minutes for complex image analysis

---

## 👤 **User Experience Design**

### **Supported Workflows:**
1. **"Analyze my base"** → Upload screenshot → Get upgrade priorities
2. **"Team suggestions"** → Upload hero roster → Get formation advice  
3. **"Resource help"** → Upload resource screen → Get optimization tips
4. **"Battle strategy"** → Upload map → Get positioning advice

### **Response Format:**
```
🖼️ **Image Analysis**: [Visual elements identified]

🧠 **Strategic Recommendations**: [Contextual advice]

🔍 **Related Knowledge**: [Knowledge base matches]

---
Sources: [Combined image + text citations]
```

---

## 📋 **Development Steps**

### **Phase 1: Core Image Support**
1. **✅ Update Settings**: Enable attachments and image comprehension
2. **✅ Add Image Detection**: Check for attachments in requests
3. **✅ Basic Image Response**: Handle image + text queries

### **Phase 2: LastZ Visual Analysis**
4. **✅ Add Image Tools**: Create LastZ-specific analysis functions  
5. **✅ Knowledge Integration**: Cross-reference visual with knowledge base
6. **✅ Enhanced Responses**: Combine image + vector search results

### **Phase 3: Testing & Deployment**
7. **✅ Test Integration**: Verify image processing works with vector search
8. **✅ Performance Testing**: Ensure no degradation with image processing
9. **✅ Deploy v0.7.8**: Beta release with image capabilities

---

## 🔍 **Key Differences from v0.7.7**

### **v0.7.7 Capabilities:**
- ✅ Vector embeddings with semantic search
- ✅ 126 knowledge items from data_index.md
- ✅ High-performance Modal infrastructure
- ✅ Clean response format with debug citations

### **v0.7.8 New Features:**
- 🆕 **Image attachment support**
- 🆕 **Visual game element identification**
- 🆕 **Multi-modal analysis (text + images)**
- 🆕 **Screenshot-based strategic advice**
- 🆕 **Enhanced user workflows**

---

## ⚠️ **Technical Considerations**

### **Performance Impact:**
- **Image Processing**: Additional compute for visual analysis
- **Response Time**: May increase due to image analysis
- **Memory Usage**: Store and process image data
- **Rate Limiting**: Consider image upload frequency

### **Error Handling:**
- **Invalid Images**: Handle non-game screenshots gracefully
- **Processing Failures**: Fallback to text-only analysis
- **Large Files**: Size limits and timeout handling
- **Network Issues**: Robust image URL access

---

## 🎯 **Success Metrics**

### **User Engagement:**
- **Image Upload Rate**: % of queries with images
- **Multi-modal Queries**: Combined text + image questions
- **User Satisfaction**: Feedback on image analysis quality

### **Technical Performance:**
- **Response Time**: Image vs text-only comparison
- **Accuracy**: Visual element identification success rate
- **Reliability**: Error rate for image processing

**Privacy Note**: This feature prioritizes user consent and data protection while building a valuable community resource for strategic insights.

## 🗂️ **v0.7.9 Planning - Image Database Feature**

### **Concept: User-Contributed Visual Knowledge Base**
Build a community-driven database of LastZ screenshots to enhance visual recognition and strategic advice.

### **Key Features:**
- **Opt-in Image Storage**: Users explicitly consent to contribute screenshots
- **Image Categorization**: Automatic sorting by screen type and game elements
- **Visual Knowledge Base**: Build searchable database of game situations
- **Community Insights**: Aggregate successful strategies from user screenshots

### **Technical Architecture:**

#### **Image Storage (Modal Volume)**
```python
# Modal volume for persistent image storage
image_volume = modal.Volume.from_name("lastz-user-images", create_if_missing=True)

@app.function(volumes={"/app/user_images": image_volume})
def store_user_image(image_url: str, user_consent: bool, metadata: dict):
    """Store user image with consent and metadata"""
    if not user_consent:
        return {"stored": False, "reason": "No user consent"}
    
    # Download and store image with metadata
    # Create searchable index entry
```

#### **Consent Management**
```python
def request_image_storage_consent(user_id: str) -> str:
    """Request user permission to store their screenshot"""
    return """
    🤝 **Help Improve LastZ Assistant**
    
    Would you like to contribute this screenshot to help other players?
    
    ✅ **If you agree:**
    - Your screenshot helps train better visual recognition
    - Other players benefit from similar strategic situations
    - All personal information is removed
    
    Reply 'yes' to contribute or 'no' to analyze privately.
    """
```

#### **Image Classification Pipeline**
```python
def classify_and_index_image(image_data: dict) -> dict:
    """Classify image and add to searchable index"""
    classification = {
        'screen_type': determine_screen_type(image_data),
        'game_elements': extract_elements(image_data),
        'strategic_context': analyze_strategy(image_data),
        'timestamp': datetime.now(),
        'user_anonymized_id': hash(user_id)  # Privacy protection
    }
    
    # Add to searchable database
    add_to_visual_index(classification)
    return classification
```

### **Privacy & Ethics:**
- **Explicit Consent**: Clear opt-in for each image
- **Data Anonymization**: Remove all personal identifiers
- **User Control**: Option to withdraw consent later
- **Transparency**: Users know how their data helps others

### **Database Schema:**
```json
{
  "image_id": "unique_hash",
  "screen_type": "base_overview",
  "elements": ["headquarters", "barracks", "mine"],
  "strategic_situation": "early_game_resource_focus",
  "success_metrics": "user_reported_outcome",
  "timestamp": "2025-10-17T10:30:00Z",
  "anonymized_user": "hash_abc123"
}
```

### **Enhanced Features for v0.7.9:**
1. **🗳️ Consent Workflow**: Streamlined permission requests
2. **📊 Visual Analytics**: Aggregate insights from stored images
3. **🎯 Situation Matching**: Find similar strategic scenarios
4. **📈 Success Tracking**: Learn from successful strategies
5. **🔍 Visual Search**: "Find bases similar to mine"

### **Implementation Timeline:**
- **Week 1**: Consent management system
- **Week 2**: Image storage and classification
- **Week 3**: Visual database indexing
- **Week 4**: Enhanced matching algorithms
- **Week 5**: Testing and privacy validation

### **Success Metrics:**
- **Consent Rate**: % of users who opt-in to contribute
- **Database Growth**: Images stored per week
- **Recognition Accuracy**: Improved visual element detection
- **User Satisfaction**: Better strategic advice quality

**Privacy Note**: This feature prioritizes user consent and data protection while building a valuable community resource for strategic insights.