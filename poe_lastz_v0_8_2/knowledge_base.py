"""Knowledge base loading and processing for Last Z Bot"""

import json
import os

# Global knowledge items list
knowledge_items = []


def load_knowledge_base():
    """Load comprehensive knowledge base from data directory (Render compatible)"""
    global knowledge_items
    knowledge_items = []

    # Track statistics for debugging
    stats = {
        "json_attempted": 0,
        "json_loaded": 0,
        "json_skipped": 0,
        "md_attempted": 0,
        "md_loaded": 0,
        "md_skipped": 0,
        "errors": [],
    }

    # Determine data path - try multiple locations for Render compatibility
    data_path_options = [
        "/mnt/data/lastz-rag/data",  # Render Disk mount point (PRODUCTION)
        "../lastz-rag/data",  # Relative path if deployed with repo
        "/app/lastz-rag/data",  # Absolute path on Render (legacy)
        "./data",  # Local development
        os.path.join(
            os.path.dirname(__file__), "..", "lastz-rag", "data"
        ),  # Relative from script location
    ]

    data_path = None
    for path in data_path_options:
        if os.path.exists(path):
            data_path = path
            print(f"✅ Found data directory: {path}")
            break

    if not data_path:
        print("❌ FATAL ERROR: Data directory not found!")
        print("❌ Searched paths:")
        for path in data_path_options:
            print(f"   - {path}")
        print("❌ Deployment failed - knowledge base required for operation")
        raise RuntimeError(
            "Knowledge base data directory not found. Cannot start bot without data."
        )

    print(f"📚 Loading knowledge base from: {data_path}")

    # Load data_index.md configuration
    data_index_path = os.path.join(data_path, "data_index.md")
    if os.path.exists(data_index_path):
        _load_from_data_index(data_path, data_index_path, stats)
    else:
        print("⚠️ data_index.md not found, using legacy loading")
        _load_legacy_hardcoded(data_path, stats)

    # Print detailed statistics
    print(f"\n{'=' * 60}")
    print("📊 KNOWLEDGE BASE LOADING SUMMARY")
    print(f"{'=' * 60}")
    print(f"✅ Total items loaded: {len(knowledge_items)}")
    print("\n📄 JSON Files:")
    print(f"   Attempted: {stats['json_attempted']}")
    print(f"   Loaded: {stats['json_loaded']}")
    print(f"   Skipped: {stats['json_skipped']}")
    print("\n📝 Markdown Files:")
    print(f"   Attempted: {stats['md_attempted']}")
    print(f"   Loaded: {stats['md_loaded']}")
    print(f"   Skipped: {stats['md_skipped']}")
    if stats["errors"]:
        print(f"\n❌ Errors ({len(stats['errors'])}):")
        for error in stats["errors"][:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(stats["errors"]) > 10:
            print(f"   ... and {len(stats['errors']) - 10} more errors")
    print(f"{'=' * 60}\n")


def _parse_data_index(data_index_path):
    """Parse data_index.md to get loading configuration"""
    try:
        with open(data_index_path, encoding="utf-8") as f:
            content = f.read()

        config = {
            "core_static": [],
            "dynamic_json_dirs": [],
            "dynamic_json_files": [],
            "dynamic_markdown_dirs": [],
        }

        # Simple parsing of YAML-like structure in markdown
        lines = content.split("\n")
        current_section = None
        current_subsection = None  # Track whether we're in directories: or files:

        for line in lines:
            # Main section detection
            if "core_static:" in line:
                current_section = "core_static"
                current_subsection = None
            elif "dynamic_json:" in line:
                current_section = "dynamic_json"
                current_subsection = None
            elif "dynamic_markdown:" in line:
                current_section = "dynamic_markdown"
                current_subsection = None
            # Subsection detection
            elif "directories:" in line:
                current_subsection = "directories"
            elif "files:" in line:
                current_subsection = "files"
            # Data extraction
            elif "- file:" in line and current_section == "core_static":
                # Extract file path
                parts = line.split('"')
                if len(parts) >= 2:
                    config["core_static"].append(parts[1])
            elif "- path:" in line and current_section == "dynamic_json":
                # Extract path from dynamic_json section
                parts = line.split('"')
                if len(parts) >= 2:
                    path = parts[1].rstrip("/")
                    if current_subsection == "directories":
                        config["dynamic_json_dirs"].append(path)
                    elif current_subsection == "files":
                        config["dynamic_json_files"].append(path)
            elif "- path:" in line and current_section == "dynamic_markdown":
                # Extract directory path from dynamic_markdown section
                parts = line.split('"')
                if len(parts) >= 2:
                    config["dynamic_markdown_dirs"].append(parts[1].rstrip("/"))

        # Debug logging
        print("🔍 Parsed data_index.md:")
        print(f"   Core static files: {len(config['core_static'])}")
        print(f"   JSON directories: {config['dynamic_json_dirs']}")
        print(f"   JSON files: {len(config['dynamic_json_files'])}")
        print(f"   Markdown directories: {config['dynamic_markdown_dirs']}")

        return config
    except Exception as e:
        print(f"❌ Error parsing data_index.md: {e}")
        return None


def _load_from_data_index(data_path, data_index_path, stats):
    """Load data based on data_index.md configuration"""
    config = _parse_data_index(data_index_path)
    if not config:
        print("⚠️ Failed to parse data_index.md, falling back to legacy loading")
        _load_legacy_hardcoded(data_path, stats)
        return

    print("📋 Parsed data_index.md configuration")

    # Load core static markdown files
    for file_path in config["core_static"]:
        full_path = os.path.join(data_path, file_path)
        stats["md_attempted"] += 1
        if os.path.exists(full_path):
            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                filename = os.path.basename(file_path)
                searchable_text = f"Core Guide: {filename.replace('.md', '').replace('_', ' ').title()} "
                searchable_text += f"Content: {content[:500]}..."

                knowledge_items.append(
                    {
                        "type": "core_guide",
                        "name": filename.replace(".md", "").replace("_", " ").title(),
                        "text": searchable_text,
                        "data": {"filename": filename, "content": content},
                    }
                )
                stats["md_loaded"] += 1
                print(f"✅ Loaded core guide: {filename}")
            except Exception as e:
                stats["md_skipped"] += 1
                stats["errors"].append(f"core/{filename}: {str(e)}")
                print(f"❌ Error loading {file_path}: {e}")
        else:
            stats["md_skipped"] += 1
            stats["errors"].append(f"core/{file_path}: File not found")

    # Load JSON directories
    for dir_name in config["dynamic_json_dirs"]:
        dir_path = os.path.join(data_path, dir_name)
        print(f"🔍 Looking for JSON directory: {dir_path}")
        if os.path.exists(dir_path):
            print(f"✅ Found directory: {dir_name}, loading...")
            _load_json_directory(dir_path, dir_name, stats)
        else:
            print(f"⚠️ Directory not found: {dir_path}")
            stats["errors"].append(
                f"JSON directory '{dir_name}' not found at {dir_path}"
            )

    # Load individual JSON files
    for file_path in config["dynamic_json_files"]:
        full_path = os.path.join(data_path, file_path)
        stats["json_attempted"] += 1
        if os.path.exists(full_path):
            try:
                with open(full_path, encoding="utf-8") as f:
                    data = json.load(f)

                filename = os.path.basename(file_path)
                _process_json_file(filename, data)
                stats["json_loaded"] += 1
                print(f"✅ Loaded JSON file: {filename}")
            except Exception as e:
                stats["json_skipped"] += 1
                stats["errors"].append(f"{file_path}: {str(e)}")
                print(f"❌ Error loading {file_path}: {e}")
        else:
            stats["json_skipped"] += 1
            stats["errors"].append(f"{file_path}: File not found")

    # Load markdown directories
    for dir_name in config["dynamic_markdown_dirs"]:
        # Check both relative to data_path and absolute
        possible_paths = [
            os.path.join(data_path, dir_name),
            os.path.join(data_path, "..", dir_name),  # For directories at repo root
            os.path.join(os.path.dirname(data_path), dir_name),
        ]

        found = False
        for dir_path in possible_paths:
            if os.path.exists(dir_path):
                print(f"✅ Found markdown directory: {dir_name} at {dir_path}")
                _load_markdown_directory(dir_path, dir_name, stats)
                found = True
                break

        if not found:
            print(f"⚠️ Markdown directory not found: {dir_name}")
            stats["errors"].append(
                f"Markdown directory '{dir_name}' not found in any search path"
            )


def _load_json_directory(dir_path, dir_name, stats):
    """Load all JSON files from a directory"""
    try:
        for filename in os.listdir(dir_path):
            if filename.endswith(".json"):
                stats["json_attempted"] += 1
                try:
                    with open(os.path.join(dir_path, filename), encoding="utf-8") as f:
                        data = json.load(f)

                    # Process based on directory type
                    if dir_name == "heroes":
                        _process_hero_file(filename, data)
                    elif dir_name == "research":
                        _process_research_file(filename, data)
                    else:
                        _process_generic_json(filename, data, dir_name)
                    stats["json_loaded"] += 1
                except Exception as e:
                    stats["json_skipped"] += 1
                    stats["errors"].append(f"{dir_name}/{filename}: {str(e)}")
                    print(f"❌ Error loading {dir_name}/{filename}: {e}")
    except Exception as e:
        stats["errors"].append(f"Reading directory {dir_path}: {str(e)}")
        print(f"❌ Error reading directory {dir_path}: {e}")


def _load_markdown_directory(dir_path, dir_name, stats):
    """Load all markdown files from a directory"""
    try:
        for filename in os.listdir(dir_path):
            if filename.endswith(".md"):
                stats["md_attempted"] += 1
                try:
                    with open(os.path.join(dir_path, filename), encoding="utf-8") as f:
                        content = f.read()

                    searchable_text = f"{dir_name.upper()} Article: {filename.replace('.md', '').replace('_', ' ').title()} "
                    searchable_text += f"Content: {content[:500]}..."

                    knowledge_items.append(
                        {
                            "type": f"{dir_name}_article",
                            "name": filename.replace(".md", "")
                            .replace("_", " ")
                            .title(),
                            "text": searchable_text,
                            "data": {
                                "filename": filename,
                                "content": content,
                                "directory": dir_name,
                            },
                        }
                    )
                    stats["md_loaded"] += 1
                    print(f"✅ Loaded {dir_name} article: {filename}")
                except Exception as e:
                    stats["md_skipped"] += 1
                    stats["errors"].append(f"{dir_name}/{filename}: {str(e)}")
                    print(f"❌ Error loading {dir_name}/{filename}: {e}")
    except Exception as e:
        stats["errors"].append(f"Reading directory {dir_path}: {str(e)}")
        print(f"❌ Error reading directory {dir_path}: {e}")


def _process_hero_file(filename, hero_data):
    """Process hero JSON files"""
    hero_text = f"Hero: {hero_data.get('name', 'Unknown')} "
    hero_text += f"Role: {hero_data.get('role', 'Unknown')} "
    hero_text += f"Rarity: {hero_data.get('rarity', 'Unknown')} "

    if "skills" in hero_data:
        skills = hero_data["skills"]
        if isinstance(skills, list):
            skill_names = []
            for skill in skills:
                if isinstance(skill, dict):
                    skill_names.append(skill.get("name", "Unknown Skill"))
                else:
                    skill_names.append(str(skill))
            hero_text += f"Skills: {' '.join(skill_names)} "
        else:
            hero_text += f"Skills: {str(skills)} "

    if "description" in hero_data:
        hero_text += f"Description: {hero_data['description']}"

    knowledge_items.append(
        {
            "type": "hero",
            "name": hero_data.get("name", filename),
            "text": hero_text,
            "data": hero_data,
        }
    )


def _process_research_file(filename, research_data):
    """Process research JSON files"""
    research_text = f"Research: {research_data.get('name', filename)} "
    research_text += f"Category: {research_data.get('category', 'Unknown')} "
    research_text += f"Description: {research_data.get('description', '')}"

    knowledge_items.append(
        {
            "type": "research",
            "name": research_data.get("name", filename),
            "text": research_text,
            "data": research_data,
        }
    )


def _process_generic_json(filename, data, directory):
    """Process generic JSON files from directories"""
    content_text = f"{directory.title()} Data: {filename} "
    content_text += (
        f"File containing {len(str(data))} characters of {directory} information"
    )

    knowledge_items.append(
        {
            "type": directory,
            "name": filename.replace(".json", "").replace("_", " ").title(),
            "text": content_text,
            "data": data,
        }
    )


def _process_json_file(filename, data):
    """Process different types of JSON files"""
    if filename == "buildings.json" and "buildings" in data:
        for building in data["buildings"]:
            building_text = f"Building: {building.get('name', 'Unknown')} "
            building_text += f"Type: {building.get('type', 'Unknown')} "
            building_text += f"Function: {building.get('function', '')} "
            if "produces" in building:
                building_text += f"Produces: {building['produces']} "
            building_text += f"Notes: {building.get('notes', '')}"

            knowledge_items.append(
                {
                    "type": "building",
                    "name": building.get("name", "Unknown"),
                    "text": building_text,
                    "data": building,
                }
            )
    elif filename == "equipment.json":
        # Handle equipment data
        equipment_items = []
        if isinstance(data, list):
            equipment_items = data
        elif "equipment" in data:
            equipment_items = data["equipment"]

        for item in equipment_items[:20]:  # Limit to avoid overwhelming
            if isinstance(item, dict):
                item_text = f"Equipment: {item.get('name', 'Unknown')} "
                item_text += f"Type: {item.get('type', 'Unknown')} "
                item_text += f"Stats: {item.get('stats', '')} "

                knowledge_items.append(
                    {
                        "type": "equipment",
                        "name": item.get("name", "Unknown"),
                        "text": item_text,
                        "data": item,
                    }
                )
    else:
        # Generic JSON file processing
        content_text = f"Data from {filename}: "
        if isinstance(data, dict):
            content_text += f"Contains keys: {', '.join(list(data.keys())[:10])}"
        elif isinstance(data, list):
            content_text += f"Contains {len(data)} items"

        knowledge_items.append(
            {
                "type": "data_file",
                "name": filename.replace(".json", "").replace("_", " ").title(),
                "text": content_text,
                "data": data,
            }
        )


def _load_legacy_hardcoded(data_path, stats):
    """Fallback to hardcoded loading if data_index.md fails"""
    print("🔄 Using legacy hardcoded data loading...")

    # Legacy core files
    core_files = [
        "game_fundamentals.md",
        "terminology.md",
        "what_is_lastz.md",
        "README.md",
    ]
    core_path = os.path.join(data_path, "core")

    if os.path.exists(core_path):
        for filename in core_files:
            filepath = os.path.join(core_path, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, encoding="utf-8") as f:
                        content = f.read()

                    searchable_text = f"Core Guide: {filename.replace('.md', '').replace('_', ' ').title()} "
                    searchable_text += f"Content: {content[:500]}..."

                    knowledge_items.append(
                        {
                            "type": "core_guide",
                            "name": filename.replace(".md", "")
                            .replace("_", " ")
                            .title(),
                            "text": searchable_text,
                            "data": {"filename": filename, "content": content},
                        }
                    )
                    print(f"✅ Loaded legacy core guide: {filename}")
                except Exception as e:
                    print(f"❌ Error loading {filename}: {e}")

    # Legacy directory scans
    for directory in ["heroes", "research"]:
        dir_path = os.path.join(data_path, directory)
        if os.path.exists(dir_path):
            _load_json_directory(dir_path, directory, stats)
