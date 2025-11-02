"""
System prompt and configuration
"""

from __future__ import annotations

import re
from pathlib import Path


def find_prompts_directory() -> Path:
    """Find the prompts directory, trying multiple locations"""
    candidates = [
        Path("poe_lastz_v0_8_2/prompts"),  # From project root
        Path("prompts"),  # Local package directory
        Path(__file__).parent / "prompts",  # Relative to this file
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            print(f"✅ Found prompts directory: {candidate}")
            return candidate

    raise RuntimeError(
        f"❌ Prompts directory not found! Tried: {candidates}. "
        "Deployment failed - prompts directory must be available."
    )


def get_available_prompts() -> dict[str, Path]:
    """Get all available prompts as a dict of name -> path"""
    prompts_dir = find_prompts_directory()
    prompt_files = sorted(prompts_dir.glob("*.md"))

    return {file.stem: file for file in prompt_files}


def detect_prompt_request(user_message: str) -> str | None:
    """Detect if user is requesting a specific prompt via !PROMPT_NAME syntax

    Example: "!TEST" or "!test" -> returns "test"
    Also supports: [TEST], {TEST}, or @TEST as fallbacks
    """
    # Try multiple patterns (in order of preference):
    # !PROMPT_NAME (primary - @ is reserved by Poe)
    # [PROMPT_NAME] (fallback)
    # {PROMPT_NAME} (fallback)
    # @PROMPT_NAME (fallback)
    patterns = [
        r"!([A-Za-z_]+)",  # !TEST
        r"\[([A-Za-z_]+)\]",  # [TEST]
        r"\{([A-Za-z_]+)\}",  # {TEST}
        r"@([A-Za-z_]+)",  # @TEST
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message)
        if match:
            requested_prompt = match.group(1).lower()
            available_prompts = get_available_prompts()

            if requested_prompt in available_prompts:
                print(f"🎯 Prompt switch requested: {requested_prompt}")
                return requested_prompt

    return None


def load_prompt_by_name(prompt_name: str) -> str:
    """Load a specific prompt by name (without .md extension)"""
    available_prompts = get_available_prompts()

    if prompt_name not in available_prompts:
        available = ", ".join(available_prompts.keys())
        raise ValueError(f"❌ Prompt '{prompt_name}' not found. Available: {available}")

    prompt_file = available_prompts[prompt_name]
    try:
        with open(prompt_file, encoding="utf-8") as f:
            content = f.read()
            print(f"✅ Loaded prompt: {prompt_name} from {prompt_file}")
            return content.strip()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load prompt {prompt_name}: {e}") from e


def load_system_prompt() -> str:
    """Load system prompt - dynamically discovers files in prompts directory"""
    prompts_dir = find_prompts_directory()

    # Find all .md files in the prompts directory
    prompt_files = sorted(prompts_dir.glob("*.md"))

    if not prompt_files:
        raise RuntimeError(
            f"❌ No prompt files found in {prompts_dir}. "
            "Deployment failed - at least one prompt file must be available."
        )

    # Prefer gamer.md as the default, fallback to first alphabetically
    default_file = prompts_dir / "gamer.md"
    if default_file.exists():
        prompt_file = default_file
    else:
        prompt_file = prompt_files[0]

    try:
        with open(prompt_file, encoding="utf-8") as f:
            content = f.read()
            print(f"✅ Loaded prompt from: {prompt_file}")
            return content.strip()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load prompt from {prompt_file}: {e}") from e
