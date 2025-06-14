import asyncio
import os
import threading
import signal
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatAction, ChatType
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Read Tokens ---
BOT_TOKENS = os.getenv("BOT_TOKENS", "").split(",")
if not BOT_TOKENS or BOT_TOKENS == [""]:
    raise ValueError("No bot tokens found. Set BOT_TOKENS environment variable.")

# Filter out empty tokens
BOT_TOKENS = [token.strip() for token in BOT_TOKENS if token.strip()]

# --- Telegram Actions List ---
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

# Global variables for bot management
running_bots = []
stop_event = asyncio.Event()

class TelegramBot:
    def __init__(self, token: str, action: ChatAction):
        self.token = token
        self.action = action
        self.app = None
        self.tasks = {}
        
    async def setup_bot(self):
        """Initialize the bot application"""
        self.app = ApplicationBuilder().token(self.token).build()
        
        # Add command handler
        self.app.add_handler(CommandHandler("start", self.start_command))
        
        # Set bot commands
        try:
            await self.app.bot.set_my_commands([
                BotCommand("start", "Show welcome message and start activity")
            ])
        except Exception as e:
            print(f"Warning: Could not set commands for bot: {e}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not update.effective_chat or not update.message:
            return
            
        chat = update.effective_chat
        message = update.message
        
        # Only respond in supported chat types
        if hasattr(chat, 'type') and chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return

        try:
            bot_username = getattr(context.bot, 'username', None) or "bot"
            add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"

            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton(text="Updates", url="https://t.me/WorkGlows"),
                    InlineKeyboardButton(text="Support", url="https://t.me/TheCryptoElders"),
                ],
                [InlineKeyboardButton(text="Add Me To Your Group", url=add_to_group_url)],
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

            if hasattr(message, 'reply_text'):
                await message.reply_text(
                    welcome_text, 
                    reply_markup=reply_markup, 
                    parse_mode="HTML"
                )

            # Start action simulation for this chat
            if hasattr(chat, 'id'):
                chat_id = chat.id
                task_key = f"action_{chat_id}"
                
                # Stop existing task if running
                if task_key in self.tasks:
                    self.tasks[task_key].cancel()
                
                # Start new action simulation task
                self.tasks[task_key] = asyncio.create_task(
                    self.simulate_action(chat_id)
                )
            
        except Exception as e:
            print(f"Error in start command: {e}")

    async def simulate_action(self, chat_id: int):
        """Continuously simulate chat action"""
        try:
            while not stop_event.is_set():
                try:
                    if self.app and hasattr(self.app, 'bot') and self.app.bot:
                        await self.app.bot.send_chat_action(chat_id=chat_id, action=self.action)
                    await asyncio.sleep(4.5)
                except Exception as e:
                    print(f"Error sending action {self.action} to chat {chat_id}: {e}")
                    await asyncio.sleep(4.5)
        except asyncio.CancelledError:
            pass

    async def start_polling(self):
        """Start the bot polling"""
        try:
            if not self.app:
                return
                
            await self.app.initialize()
            await self.app.start()
            
            # Get bot info
            if hasattr(self.app, 'bot') and self.app.bot:
                bot_user = await self.app.bot.get_me()
                print(f"Bot @{bot_user.username} is running with action {self.action}")
            
            # Start polling
            if hasattr(self.app, 'updater') and self.app.updater:
                await self.app.updater.start_polling()
            
            # Keep running until stop event
            while not stop_event.is_set():
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error in bot polling: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up bot resources"""
        try:
            # Cancel all tasks
            for task in self.tasks.values():
                task.cancel()
            
            if self.app:
                if hasattr(self.app, 'updater') and self.app.updater:
                    await self.app.updater.stop()
                if hasattr(self.app, 'stop'):
                    await self.app.stop()
                if hasattr(self.app, 'shutdown'):
                    await self.app.shutdown()
        except Exception as e:
            print(f"Error during cleanup: {e}")

async def run_single_bot(token: str, action: ChatAction):
    """Run a single bot instance"""
    bot = TelegramBot(token, action)
    running_bots.append(bot)
    
    try:
        await bot.setup_bot()
        await bot.start_polling()
    except Exception as e:
        print(f"Error running bot with token {token[:10]}...: {e}")

async def main():
    """Start all bots concurrently"""
    # Limit the number of bots to available actions
    tokens_to_use = BOT_TOKENS[:len(ACTIONS)]
    actions_to_use = ACTIONS[:len(tokens_to_use)]
    
    # Create tasks for each bot
    tasks = []
    for token, action in zip(tokens_to_use, actions_to_use):
        task = asyncio.create_task(run_single_bot(token, action))
        tasks.append(task)
    
    try:
        # Wait for all bots to run
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        print("Shutting down bots...")
        stop_event.set()
        
        # Cleanup all bots
        for bot in running_bots:
            await bot.cleanup()

# --- HTTP Server for Health Checks ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telegram multi-bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress log messages
        pass

def start_dummy_server():
    """Start HTTP server for health checks"""
    port = int(os.environ.get("PORT", 5000))
    try:
        server = HTTPServer(("0.0.0.0", port), DummyHandler)
        print(f"Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Error starting health server: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("Received shutdown signal")
    stop_event.set()
    sys.exit(0)

# --- Entry Point ---
if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start health check server in background
    health_thread = threading.Thread(target=start_dummy_server, daemon=True)
    health_thread.start()
    
    # Run the main bot application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application interrupted")
    except Exception as e:
        print(f"Application error: {e}")