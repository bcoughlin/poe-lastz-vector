"""
Local Data POC based on working minimal pattern
Testing Modal's .add_local_dir() with proper Poe bot structure
"""

import os
from collections.abc import AsyncIterable

from modal import App, Image, asgi_app

import fastapi_poe as fp

# Bot credentials
bot_access_key = "Z0v6PH9jrhaapEZYrmxO4jnKeJUggiNq"
bot_name = "LocalDataPOC"


class LocalDataPOCBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        """Test if we can access local mounted data"""
        try:
            # Test 1: Check if directory exists
            data_dir = "/app/data"
            if not os.path.exists(data_dir):
                yield fp.PartialResponse(text="❌ /app/data directory not found")
                return

            # Test 2: List contents
            contents = os.listdir(data_dir)

            # Test 3: Try to read data_index.md
            index_path = "/app/data/core/data_index.md"
            if os.path.exists(index_path):
                with open(index_path) as f:
                    content = f.read()[:200]  # First 200 chars

                response = f"""✅ Local data mount SUCCESS!

📁 Data directory contents: {contents}

📄 Found data_index.md with content:
{content}...

🎉 Local mounting is working perfectly!"""
            else:
                response = f"""⚠️ Directory exists but data_index.md missing.
Contents: {contents}"""

        except Exception as e:
            response = f"❌ Error accessing local data: {e}"

        yield fp.PartialResponse(text=response)

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"Claude-3.5-Sonnet": 1},
            allow_attachments=False,
            introduction_message="🧪 **Local Data Test Bot**\n\nTesting Modal's local data mounting capability.\n\nSay anything to test if I can access locally mounted data files!",
        )


# Modal setup with local data mounting
REQUIREMENTS = ["fastapi-poe"]
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env({"POE_ACCESS_KEY": bot_access_key, "POE_BOT_NAME": bot_name})
    .add_local_dir(
        "/Users/bradleycoughlin/local_code/lastz-rag/data", remote_path="/app/data"
    )
)
app = App("local-data-poc")


@app.function(image=image)
@asgi_app()
def fastapi_app():
    bot = LocalDataPOCBot()
    app = fp.make_app(
        bot,
        access_key=bot_access_key,
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name),
    )
    return app


if __name__ == "__main__":
    # Local test
    print("🧪 Testing local data access...")
    data_path = "/Users/bradleycoughlin/local_code/lastz-rag/data/core/data_index.md"
    if os.path.exists(data_path):
        print("✅ Local data file exists")
        with open(data_path) as f:
            print(f"📄 Content preview: {f.read()[:100]}...")
    else:
        print("❌ Local data file not found")
