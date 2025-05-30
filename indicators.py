import asyncio
import os
from telegram import Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Read tokens from environment variable
BOT_TOKENS = os.getenv("BOT_TOKENS", "").split(",")
if not BOT_TOKENS or BOT_TOKENS == [""]:
    raise ValueError("No bot tokens found. Set BOT_TOKENS environment variable.")

# All available Telegram chat indicators
ACTIONS = [
    ChatAction.TYPING,
    ChatAction.UPLOAD_PHOTO,
    ChatAction.RECORD_VIDEO,
    ChatAction.UPLOAD_VIDEO,
    ChatAction.RECORD_VOICE,
    ChatAction.UPLOAD_VOICE,
    ChatAction.UPLOAD_DOCUMENT,
    ChatAction.CHOOSE_STICKER,
    ChatAction.FIND_LOCATION,
    ChatAction.RECORD_VIDEO_NOTE,
    ChatAction.UPLOAD_VIDEO_NOTE,
]

async def simulate_action(chat_id: int, app, action: ChatAction):
    try:
        while True:
            await app.bot.send_chat_action(chat_id=chat_id, action=action)
            await asyncio.sleep(4.5)
    except asyncio.CancelledError:
        pass

async def create_handler(action: ChatAction):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return
        chat_id = chat.id
        task_key = f"{context.bot.token}_{chat_id}"
        if task_key not in context.application.chat_data:
            context.application.chat_data[task_key] = asyncio.create_task(
                simulate_action(chat_id, context.application, action)
            )
    return handler

async def run_bot(token, action):
    app = ApplicationBuilder().token(token).build()
    handler = await create_handler(action)
    app.add_handler(MessageHandler(filters.TEXT, handler))
    print(f"Bot with token {token[:8]}... is running")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    return app

async def main():
    apps = await asyncio.gather(*(run_bot(t, a) for t, a in zip(BOT_TOKENS, ACTIONS)))
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
