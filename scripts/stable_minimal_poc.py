"""
Stable minimal POC based on official Poe echobot example
"""

from collections.abc import AsyncIterable

from modal import App, Image, asgi_app

import fastapi_poe as fp

# Bot credentials
bot_access_key = "fHOVJ4FhxmC0kiM6GV6o5DpZxk8efEe5"
bot_name = "MinimalPOC"


class MinimalPOCBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        last_message = request.query[-1].content
        yield fp.PartialResponse(text=f"Minimal POC Echo: {last_message}")


# Modal setup
REQUIREMENTS = ["fastapi-poe"]
image = (
    Image.debian_slim()
    .pip_install(*REQUIREMENTS)
    .env({"POE_ACCESS_KEY": bot_access_key, "POE_BOT_NAME": bot_name})
)
app = App("stable-minimal-poc")


@app.function(image=image)
@asgi_app()
def fastapi_app():
    bot = MinimalPOCBot()
    app = fp.make_app(
        bot,
        access_key=bot_access_key,
        bot_name=bot_name,
        allow_without_key=not (bot_access_key and bot_name),
    )
    return app
