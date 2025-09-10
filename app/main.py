import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from botbuilder.core import (
    BotFrameworkAdapterSettings, TurnContext, ConversationState, MemoryStorage
)
from botbuilder.integration.aiohttp import BotFrameworkHttpAdapter
from botbuilder.schema import Activity, ActivityTypes
from command_router import handle_command

load_dotenv()

app = FastAPI()

settings = BotFrameworkAdapterSettings(
    app_id=os.getenv("MicrosoftAppId"), # pyright: ignore[reportArgumentType]
    app_password=os.getenv("MicrosoftAppPassword"), # pyright: ignore[reportArgumentType]
)
adapter = BotFrameworkHttpAdapter(settings)
memory = MemoryStorage()
conversation_state = ConversationState(memory)

@app.post("/api/messages")
async def messages(req: Request):
    body = await req.json()
    activity = Activity().deserialize(body)

    async def bot_logic(turn_context: TurnContext):
        if turn_context.activity.type == ActivityTypes.message:
            text = (turn_context.activity.text or "").strip()
            # Teams often prefixes bot mentions; strip "<at>Bot</at>" etc.
            t = " ".join(token for token in text.split() if not token.startswith("<at"))
            result = await handle_command(t, turn_context)
            if isinstance(result, str) and result:
                await turn_context.send_activity(result)
        else:
            await turn_context.send_activity("👋")

    resp: Response = Response(status_code=200)
    await adapter.process_activity(activity, "", bot_logic)
    return resp
