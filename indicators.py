import asyncio
import os
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatAction, ChatType
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer

# ───── Load Tokens and Define Actions ─────
BOT_TOKENS = os.getenv("BOT_TOKENS", "").split(",")
if not BOT_TOKENS or BOT_TOKENS == [""]:
    raise ValueError("No bot tokens found. Set BOT_TOKENS environment variable.")

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

# ───── Simulate Chat Actions Loop ─────
async def simulate_action(chat_id: int, app, action: ChatAction):
    try:
        while True:
            await app.bot.send_chat_action(chat_id=chat_id, action=action)
            await asyncio.sleep(4.5)
    except asyncio.CancelledError:
        pass

# ───── Bot Setup ─────
async def run_bot(token, action: ChatAction):
    app = ApplicationBuilder().token(token).build()

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return

        bot_username = context.bot.username
        add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"

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

        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

        chat_id = chat.id
        task_key = f"{context.bot.token}_{chat_id}"
        if task_key not in context.chat_data:
            context.chat_data[task_key] = asyncio.create_task(
                simulate_action(chat_id, context.application, action)
            )

    app.add_handler(CommandHandler("start", start))

    await app.initialize()
    await app.bot.set_my_commands([BotCommand("start", "Show welcome message")])
    bot_user = await app.bot.get_me()
    print(f"Started bot: @{bot_user.username}")

    await app.start()
    await app.run_polling(close_loop=False)  # ✅ FIX: don't close the global loop

# ───── Dummy Server for Render ─────
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

# ───── Entrypoint ─────
async def main():
    await asyncio.gather(*(run_bot(token, action) for token, action in zip(BOT_TOKENS, ACTIONS)))

if __name__ == "__main__":
    threading.Thread(target=start_dummy_server, daemon=True).start()
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            # Fallback for environments where loop is already running
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise