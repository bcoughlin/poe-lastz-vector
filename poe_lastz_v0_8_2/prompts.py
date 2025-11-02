"""
System prompt and configuration
"""

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

    # Load the first prompt file found (alphabetically)
    prompt_file = prompt_files[0]
    try:
        with open(prompt_file, encoding="utf-8") as f:
            content = f.read()
            print(f"✅ Loaded prompt from: {prompt_file}")
            return content.strip()
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load prompt from {prompt_file}: {e}") from e
