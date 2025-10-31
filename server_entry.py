#!/usr/bin/env python3
"""
Dynamic Server Entry Point for Poe LastZ Bot
Automatically detects and loads the latest version from poe_lastz_v* directories
"""

import importlib.util
import os
import re
import sys
from pathlib import Path


def find_latest_version():
    """Find the latest poe_lastz_v* directory and return the module path"""
    current_dir = Path(__file__).parent
    
    # Find all poe_lastz_v* directories
    version_dirs = []
    pattern = re.compile(r'^poe_lastz_v(\d+)_(\d+)_(\d+)$')
    
    for item in current_dir.iterdir():
        if item.is_dir() and pattern.match(item.name):
            match = pattern.match(item.name)
            if match:
                # Convert version to tuple for sorting: (major, minor, patch)
                version_tuple = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
                version_dirs.append((version_tuple, item))
    
    if not version_dirs:
        raise RuntimeError("No poe_lastz_v* directories found!")
    
    # Sort by version tuple and get the latest
    version_dirs.sort(key=lambda x: x[0], reverse=True)
    latest_version, latest_dir = version_dirs[0]
    
    print(f"🚀 Auto-detected latest version: {latest_dir.name} (v{'.'.join(map(str, latest_version))})")
    
    return latest_dir


def load_latest_server():
    """Dynamically import and return the app from the latest version"""
    latest_dir = find_latest_version()
    server_path = latest_dir / "server.py"
    
    if not server_path.exists():
        raise RuntimeError(f"server.py not found in {latest_dir}")
    
    # Add the version directory to Python path so imports work
    sys.path.insert(0, str(latest_dir))
    
    # Create a symlink-like module mapping for imports
    # This allows the versioned server.py to import its modules as if they were at root
    
    # Map the version directory modules to the expected import paths
    version_name = latest_dir.name
    
    # Load knowledge_base module from version directory
    kb_spec = importlib.util.spec_from_file_location(
        f"{version_name}.knowledge_base", 
        latest_dir / "knowledge_base.py"
    )
    kb_module = importlib.util.module_from_spec(kb_spec)
    kb_spec.loader.exec_module(kb_module)
    sys.modules[f"{version_name}.knowledge_base"] = kb_module
    
    # Load logger module  
    logger_spec = importlib.util.spec_from_file_location(
        f"{version_name}.logger",
        latest_dir / "logger.py" 
    )
    logger_module = importlib.util.module_from_spec(logger_spec)
    logger_spec.loader.exec_module(logger_module)
    sys.modules[f"{version_name}.logger"] = logger_module
    
    # Load prompts module
    prompts_spec = importlib.util.spec_from_file_location(
        f"{version_name}.prompts",
        latest_dir / "prompts.py"
    )
    prompts_module = importlib.util.module_from_spec(prompts_spec) 
    prompts_spec.loader.exec_module(prompts_module)
    sys.modules[f"{version_name}.prompts"] = prompts_module
    
    # Also make them available as bot_symlink.* for backwards compatibility
    sys.modules["bot_symlink.knowledge_base"] = kb_module
    sys.modules["bot_symlink.logger"] = logger_module  
    sys.modules["bot_symlink.prompts"] = prompts_module
    
    # Now import the server module
    spec = importlib.util.spec_from_file_location("dynamic_server", server_path)
    server_module = importlib.util.module_from_spec(spec)
    
    # Execute the module
    spec.loader.exec_module(server_module)
    
    # Return the FastAPI app
    if hasattr(server_module, 'app'):
        print(f"✅ Loaded FastAPI app from {latest_dir.name}")
        return server_module.app
    else:
        raise RuntimeError(f"No 'app' attribute found in {server_path}")


# Load the app from the latest version
try:
    app = load_latest_server()
    print("🎯 Dynamic server loading complete!")
except Exception as e:
    print(f"❌ Failed to load server: {e}")
    raise