import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatAction, ChatType
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

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

# ------------- Simulate “typing”/“uploading” actions -------------
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

# ------------- /start Command Handler -------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a welcome message with inline buttons:
      • Updates (links to your channel)
      • Support (links to your group chat)
      • Add Me To Your Group (bot’s ‘add to group’ link)
    """
    # 1st row: Updates, Support
    # 2nd row: Add Me To Your Group
    keyboard = [
        [
            InlineKeyboardButton(text="Updates", url="https://t.me/YOUR_CHANNEL_URL"),
            InlineKeyboardButton(text="Support", url="https://t.me/YOUR_SUPPORT_GROUP_URL"),
        ],
        [
            InlineKeyboardButton(
                text="Add Me To Your Group",
                url="https://t.me/YOUR_BOT_USERNAME?startgroup=true",
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "👋 Hello! I’m your friendly bot. Here’s what I can do:\n\n"
        "• I’ll keep you updated with the latest news and alerts.\n"
        "• Need help? Use the Support button below.\n"
        "• Add me to your own group so I can assist everyone there.\n\n"
        "Just tap one of the buttons below to get started!"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# ------------- Helper to set /start in the commands menu -------------
async def set_bot_commands(app):
    """
    Register the /start command so it appears in Telegram’s command menu.
    """
    commands = [
        BotCommand(command="start", description="Show welcome message & buttons"),
    ]
    await app.bot.set_my_commands(commands)

# ------------- Run a single bot instance -------------
async def run_bot(token, action):
    app = ApplicationBuilder().token(token).build()

    # 1) Register the /start handler
    app.add_handler(CommandHandler("start", start))

    # 2) Register the "simulate activity" handler for all text messages
    handler = await create_handler(action)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handler))

    # 3) Set /start in the commands menu
    #    We do this after building the app but before starting it.
    await set_bot_commands(app)

    print(f"Bot with token {token[:8]}... is running")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    return app

# ------------- Main entrypoint -------------
async def main():
    # Launch one Application per BOT_TOKEN + ChatAction
    apps = await asyncio.gather(
        *(run_bot(token, action) for token, action in zip(BOT_TOKENS, ACTIONS))
    )

    # Keep the script alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())