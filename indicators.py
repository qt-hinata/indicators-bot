import asyncio
import os
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatAction
from telegram.enums import ChatType
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer

# ------------- Telegram‐bot SETUP -------------
# Read tokens from environment variable (comma-separated)
BOT_TOKENS = os.getenv("BOT_TOKENS", "").split(",")
if not BOT_TOKENS or BOT_TOKENS == [""]:
    raise ValueError("No bot tokens found. Set BOT_TOKENS environment variable.")

# All available Telegram chat indicators (PTB v20+)
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

# ------------- Run a single bot instance -------------
async def run_bot(token: str, action: ChatAction):
    # Build the Application
    app = ApplicationBuilder().token(token).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return

        # Build the “Add Me To Your Group” URL
        add_to_group_url = f"https://t.me/{context.bot.username}?startgroup=true"

        keyboard = [
            [
                InlineKeyboardButton(text="Updates", url="https://t.me/WorkGlows"),
                InlineKeyboardButton(text="Support", url="https://t.me/TheCryptoElders"),
            ],
            [
                InlineKeyboardButton(text="Add Me To Your Group", url=add_to_group_url),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        welcome_text = (
            "👋 Hello! I'm here to keep your group active and engaging.\n\n"
            "✨ <b>What I do:</b>\n"
            "• Simulate typing, uploading, and more to boost visibility\n"
            "• Help maintain conversation flow in your groups\n"
            "• Super simple to set up—just add and go!\n\n"
            "🚀 <b>Tap /start to begin the magic.</b>\n"
            "👇 Or use the buttons below for support and adding me to your group!"
        )
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        # Prevent duplicate tasks per chat
        task_key = f"sim_task_{chat.id}"
        if task_key not in context.chat_data:
            context.chat_data[task_key] = asyncio.create_task(
                simulate_action(chat.id, context.application, action)
            )

    # Register handlers
    app.add_handler(CommandHandler("start", start))

    # Initialize application and set commands menu
    await app.initialize()
    await app.bot.set_my_commands([
        BotCommand(command="start", description="Show welcome & buttons")
    ])

    # Print which bot is running
    bot_user = await app.bot.get_me()
    print(f"Bot with token {token[:8]}... is running as @{bot_user.username}")

    # Start polling (in PTB v20+ you can also use `await app.run_polling()`)
    await app.start()
    await app.updater.start_polling()

    # Keep this bot running until cancelled
    await app.idle()

# ------------- Main entrypoint -------------
async def main():
    # Ensure we only start as many bots as we have actions
    instances = [
        run_bot(token, action)
        for token, action in zip(BOT_TOKENS, ACTIONS)
    ]
    await asyncio.gather(*instances)

# ─── Dummy HTTP Server to Keep Render Happy ─────────────────────────────────
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"AFK bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def start_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy server listening on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    # Launch the dummy HTTP health-check server
    threading.Thread(target=start_dummy_server, daemon=True).start()
    # Run all bot instances
    asyncio.run(main())