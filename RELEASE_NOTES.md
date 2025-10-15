# Last Z Bot Release Notes

## v7.3 - Dynamic Loading Architecture (2025-10-15)

### 🚀 Major Features
- **Pure Dynamic Data Loading**: Complete removal of static LASTZ_KNOWLEDGE fallback
- **Modal Volume Integration**: Loads all data from `lastz-data` volume mounted at `/app/data`
- **Index-Driven Discovery**: Uses `data_index.md` for automatic file discovery and loading
- **Hybrid Data Sources**: Supports markdown, JSON files and directories
- **No Fallback Philosophy**: Returns clear error messages instead of masking loading failures

### 🏗️ Architecture Changes
- **Volume Mount**: `lastz_data_volume` mounted at `/app/data`
- **Dynamic Parser**: Supports markdown headers, bullet points, bold text extraction
- **JSON Handler**: Handles both dict/list structures with intelligent text generation
- **YAML Configuration**: Parses YAML blocks from data_index.md for loading instructions
- **Error Transparency**: "No knowledge available - dynamic loading failed" instead of static fallbacks

### 🔧 Technical Implementation
- `load_all_knowledge()`: Main dynamic loading orchestrator
- `parse_data_index()`: YAML configuration parser from markdown
- `parse_json_file()`: Converts JSON data to knowledge format with tags
- `parse_markdown_file()`: Extracts headers, bullets, and bold text as knowledge items
- Vector search initialization uses dynamic knowledge exclusively

### 📁 Data Structure Support
```
/app/data/
├── core/
│   ├── data_index.md      # Loading configuration (YAML blocks)
│   ├── game_fundamentals.md
│   └── terminology.md
├── heroes/                # Auto-discovered JSON files
├── buildings/             # Auto-discovered JSON files
└── research/              # Auto-discovered markdown files
```

### 🛠️ Deployment Requirements
**CRITICAL**: Volume must be populated before deployment:
```bash
cd /Users/bradleycoughlin/local_code
modal volume put lastz-data lastz-rag/data /
```

### 🐛 Known Issues & Debugging
- Returns "No knowledge available" if volume mount fails
- Clear error messages for YAML parsing failures
- Vector search falls back to keyword search if sentence-transformers fails
- All loading errors logged with specific file paths and error details

### 🔬 Testing Strategy
- No static fallbacks ensure real dynamic loading verification
- Error messages clearly indicate loading stage failures
- Vector search vs keyword search fallback logging
- Volume mount verification through file existence checks

---

## v7.2 - Initial Dynamic Loading Attempt (2025-10-15)

### ⚠️ Deprecated - Static Fallback Issues
- Had LASTZ_KNOWLEDGE fallback that masked loading failures
- Incomplete error handling
- Mixed static/dynamic approach caused confusion

---

## v7.1 - Working Tool-Based Architecture (2025-10-15)

### ✅ Stable Foundation
- GPT-5 tool calling working in Poe
- Unicode sanitization resolved
- Vector search with sentence-transformers
- Tool definitions: extract_player_data, get_personalized_advice, get_lastz_knowledge
- Modal deployment with cache-busted app names

### 🔧 Technical Stack
- fastapi-poe==0.0.48
- sentence-transformers 'all-MiniLM-L6-v2'
- Modal serverless deployment
- scikit-learn for cosine similarity

---

## v7.0 - Clean Architecture Baseline (2025-10-15)

### 🎯 Project Goals
- Clean tool-based architecture
- Remove manual extraction complexity
- Pure GPT-5 driven interactions
- Vector search foundation

### 🏗️ Core Components
- LastZCleanBot class structure
- Tool-based response handling
- Vector search initialization framework
- Modal deployment configuration