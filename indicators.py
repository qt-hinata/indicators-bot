import asyncio
import os
import threading
import signal
import sys
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ChatAction, ChatType
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from http.server import BaseHTTPRequestHandler, HTTPServer

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
stop_event = threading.Event()

class RenderTelegramBot:
    def __init__(self, token: str, action: ChatAction):
        self.token = token
        self.action = action
        self.app = None
        self.tasks = {}
        
    def build_app(self):
        """Build the application with error handling"""
        try:
            self.app = ApplicationBuilder().token(self.token).build()
            self.app.add_handler(CommandHandler("start", self.start_command))
            logger.info(f"Bot application built successfully for action {self.action}")
            return True
        except Exception as e:
            logger.error(f"Failed to build bot application: {e}")
            return False
    
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

            await message.reply_text(
                welcome_text, 
                reply_markup=reply_markup, 
                parse_mode="HTML"
            )

            # Start action simulation for this chat
            chat_id = chat.id
            task_key = f"action_{chat_id}"
            
            # Stop existing task if running
            if task_key in self.tasks:
                self.tasks[task_key].cancel()
            
            # Start new action simulation task
            self.tasks[task_key] = asyncio.create_task(
                self.simulate_action(chat_id)
            )
            
            logger.info(f"Started action simulation for chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")

    async def simulate_action(self, chat_id: int):
        """Continuously simulate chat action"""
        try:
            while not stop_event.is_set():
                try:
                    if self.app and hasattr(self.app, 'bot') and self.app.bot:
                        await self.app.bot.send_chat_action(chat_id=chat_id, action=self.action)
                    await asyncio.sleep(4.5)
                except Exception as e:
                    logger.debug(f"Error sending action {self.action} to chat {chat_id}: {e}")
                    await asyncio.sleep(4.5)
        except asyncio.CancelledError:
            logger.info(f"Action simulation cancelled for chat {chat_id}")

    def run_with_retry(self):
        """Run bot with retry mechanism for Render compatibility"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries and not stop_event.is_set():
            try:
                logger.info(f"Starting bot (attempt {retry_count + 1}/{max_retries})")
                
                # Use the simplest possible polling method
                self.app.run_polling(
                    poll_interval=1.0,
                    timeout=10,
                    bootstrap_retries=3,
                    read_timeout=10,
                    write_timeout=10,
                    connect_timeout=10,
                    pool_timeout=10,
                    drop_pending_updates=True
                )
                
                # If we get here, polling started successfully
                logger.info(f"Bot with action {self.action} started successfully")
                break
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Bot startup failed (attempt {retry_count}): {e}")
                
                if retry_count < max_retries:
                    logger.info(f"Retrying in 5 seconds...")
                    import time
                    time.sleep(5)
                else:
                    logger.error(f"Bot failed to start after {max_retries} attempts")

def run_single_bot(token: str, action: ChatAction):
    """Run a single bot instance"""
    bot = RenderTelegramBot(token, action)
    running_bots.append(bot)
    
    try:
        if bot.build_app():
            bot.run_with_retry()
    except Exception as e:
        logger.error(f"Critical error running bot: {e}")

def main():
    """Start all bots in separate threads"""
    tokens_to_use = BOT_TOKENS[:len(ACTIONS)]
    actions_to_use = ACTIONS[:len(tokens_to_use)]
    
    threads = []
    for i, (token, action) in enumerate(zip(tokens_to_use, actions_to_use)):
        # Stagger bot starts to avoid conflicts
        if i > 0:
            import time
            time.sleep(2)
            
        thread = threading.Thread(
            target=run_single_bot, 
            args=(token, action),
            daemon=True,
            name=f"Bot-{action}"
        )
        threads.append(thread)
        thread.start()
        logger.info(f"Started thread for bot with action {action}")
    
    try:
        # Keep main thread alive
        while not stop_event.is_set():
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down bots...")
        stop_event.set()

# --- HTTP Server for Health Checks ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        
        status = f"Telegram Multi-Bot Status\n"
        status += f"Active bots: {len(running_bots)}\n"
        status += f"Configured tokens: {len(BOT_TOKENS)}\n"
        status += f"Health check: OK\n"
        
        self.wfile.write(status.encode())

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress HTTP server logs

def start_health_server():
    """Start HTTP server for Render health checks"""
    port = int(os.environ.get("PORT", 5000))
    
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal")
    stop_event.set()
    
    # Give threads time to cleanup
    import time
    time.sleep(2)
    sys.exit(0)

# --- Entry Point ---
if __name__ == "__main__":
    logger.info("Starting Telegram Multi-Bot for Render deployment")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start health check server
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Start bot application
    try:
        main()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)