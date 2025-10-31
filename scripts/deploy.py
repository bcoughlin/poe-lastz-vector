#!/usr/bin/env python3
"""
Deployment script for Poe bots with discrete environment variables.
"""

import os
import subprocess
import sys
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Please create one with your bot credentials.")
        return False

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

    print("✅ Environment variables loaded from .env")
    return True


def deploy_bot(bot_name: str, app_name: str):
    """Deploy a specific bot to Modal."""
    print(f"\n🚀 Deploying {bot_name}...")

    # Check if required environment variables are set
    if bot_name == "lastz":
        access_key = os.getenv("POE_ACCESS_KEY_LASTZ")
        bot_name_env = os.getenv("POE_BOT_NAME_LASTZ")
        file_name = "lastz_game_bot.py"
    elif bot_name == "echo":
        access_key = os.getenv("POE_ACCESS_KEY_ECHO")
        bot_name_env = os.getenv("POE_BOT_NAME_ECHO")
        file_name = "echobot.py"
    else:
        print(f"❌ Unknown bot: {bot_name}")
        return False

    if not access_key:
        print(
            f"⚠️  No access key found for {bot_name} bot - deploying without credentials"
        )
    else:
        print(f"✅ Access key configured for {bot_name} bot: {bot_name_env}")

    # Deploy using Modal
    try:
        result = subprocess.run(
            ["modal", "deploy", file_name], check=True, capture_output=True, text=True
        )

        print(f"✅ {bot_name.title()} bot deployed successfully!")
        if result.stdout:
            print(result.stdout)
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy {bot_name} bot:")
        print(e.stderr)
        return False


def main():
    """Main deployment script."""
    print("🤖 Poe Bot Deployment Manager")
    print("=" * 40)

    # Load environment variables
    if not load_env_file():
        sys.exit(1)

    # Get deployment target
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target in ["lastz", "echo", "both"]:
            if target == "both":
                success = deploy_bot("lastz", "lastz-game-bot")
                success &= deploy_bot("echo", "poe-echo-bot")
            else:
                success = deploy_bot(
                    target,
                    f"{'lastz-game-bot' if target == 'lastz' else 'poe-echo-bot'}",
                )

            if success:
                print("\n🎉 Deployment complete!")
            else:
                print("\n💥 Deployment failed!")
                sys.exit(1)
        else:
            print(f"❌ Invalid target: {target}")
            print("Usage: python deploy.py [lastz|echo|both]")
            sys.exit(1)
    else:
        print("Usage: python deploy.py [lastz|echo|both]")
        print("\nAvailable bots:")
        print("  lastz - Last Z Game Analysis Bot")
        print("  echo  - Simple Echo Bot")
        print("  both  - Deploy both bots")


if __name__ == "__main__":
    main()
