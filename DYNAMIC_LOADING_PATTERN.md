# Dynamic Knowledge Loading Pattern

## Implementation in Poe Bot

```python
def load_all_knowledge(self):
    """Load all knowledge dynamically based on data_index.md"""
    knowledge = []
    
    # 1. Parse data index to get loading instructions
    data_index = self.parse_data_index("/app/data/core/data_index.md")
    
    # 2. Load core static files (priority order)
    for core_file in data_index["core_static"]:
        file_path = f"/app/data/core/{core_file['file']}"
        if os.path.exists(file_path):
            knowledge.extend(self.parse_markdown_file(file_path))
    
    # 3. Load dynamic JSON files
    for json_file in data_index["dynamic_json"]["files"]:
        file_path = f"/app/data/{json_file['path']}"
        if os.path.exists(file_path):
            knowledge.extend(self.parse_json_file(file_path, json_file["description"]))
    
    # 4. Load dynamic JSON directories  
    for json_dir in data_index["dynamic_json"]["directories"]:
        dir_path = f"/app/data/{json_dir['path']}"
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.json'):
                    knowledge.extend(self.parse_json_file(f"{dir_path}/{filename}", json_dir["description"]))
    
    # 5. Load dynamic markdown directories
    for md_dir in data_index["dynamic_markdown"]["directories"]:
        dir_path = f"/app/data/{md_dir['path']}"
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.md'):
                    knowledge.extend(self.parse_markdown_file(f"{dir_path}/{filename}"))
    
    return knowledge

def parse_data_index(self, index_path):
    """Parse the data_index.md file to get loading instructions"""
    # Simple YAML-in-markdown parser or use actual YAML
    # Returns structured data about what to load
    pass

def parse_json_file(self, file_path, description):
    """Convert JSON data to knowledge format"""
    try:
        with open(file_path) as f:
            data = json.load(f)
            return self.json_to_knowledge(data, description)
    except Exception as e:
        print(f"Failed to load {file_path}: {e}")
        return []

def parse_markdown_file(self, file_path):
    """Convert markdown to knowledge format"""
    try:
        with open(file_path) as f:
            content = f.read()
            return self.markdown_to_knowledge(content)
    except Exception as e:
        print(f"Failed to load {file_path}: {e}")
        return []
```

## Benefits

✅ **No hardcoded filenames** - All discovery is dynamic  
✅ **Auto-discovery** - New files automatically included  
✅ **Configurable** - Add new sources by updating data_index.md  
✅ **Error resilient** - Missing files don't break loading  
✅ **Priority control** - Core files loaded first  
✅ **Type-aware** - Different processing for JSON vs Markdown

## Adding New Data Sources

Just update `data_index.md`:
```yaml
# Add new JSON file
- path: "new_feature.json"
  type: "json_single"  
  description: "New game feature data"

# Add new directory
- path: "events/"
  type: "json_collection"
  description: "Event and seasonal data"
```

No code changes needed!