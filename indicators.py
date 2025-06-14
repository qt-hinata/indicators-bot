"""
Telegram Multi-Bot Service for Render Deployment
Compatible with python-telegram-bot v20.7 - simulates chat actions to keep groups active
"""

import asyncio
import os
import logging
import signal
import sys
import threading
from typing import Dict, List, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

# Configure logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import telegram components with error handling
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
    from telegram.constants import ChatAction, ChatType
    from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
    from telegram.error import NetworkError, BadRequest, TelegramError
    logger.info("Telegram imports successful")
except ImportError as e:
    logger.error(f"Cannot import telegram library: {e}")
    logger.error("Please ensure python-telegram-bot is properly installed")
    sys.exit(1)

# Reduce external library noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Environment configuration
BOT_TOKENS = os.getenv("BOT_TOKENS", "").split(",")
if not BOT_TOKENS or BOT_TOKENS == [""]:
    logger.error("BOT_TOKENS environment variable is required")
    logger.error("Set BOT_TOKENS with comma-separated bot tokens")
    sys.exit(1)

BOT_TOKENS = [token.strip() for token in BOT_TOKENS if token.strip()]
if not BOT_TOKENS:
    logger.error("No valid bot tokens found in BOT_TOKENS")
    sys.exit(1)

# Available chat actions for simulation
CHAT_ACTIONS = [
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

# Global state
bot_instances: List['TelegramBot'] = []
shutdown_event = threading.Event()
health_server = None


class TelegramBot:
    """Individual Telegram bot instance with action simulation capabilities"""
    
    def __init__(self, token: str, action: ChatAction):
        self.token = token
        self.action = action
        self.app: Optional[Application] = None
        self.active_simulations: Dict[int, asyncio.Task] = {}
        self.is_running = False
        self.bot_info = None
        
    async def initialize(self) -> bool:
        """Initialize the bot application and configure handlers"""
        try:
            # Build the application
            self.app = ApplicationBuilder().token(self.token).build()
            
            # Add command handlers
            self.app.add_handler(CommandHandler("start", self.handle_start_command))
            
            # Initialize application
            await self.app.initialize()
            
            # Get bot information
            self.bot_info = await self.app.bot.get_me()
            
            # Set bot commands in menu
            commands = [BotCommand("start", "Activate bot and start group activity simulation")]
            await self.app.bot.set_my_commands(commands)
            
            logger.info(f"Bot @{self.bot_info.username} initialized for {self.action}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot for {self.action}: {e}")
            return False
    
    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not update.effective_chat or not update.message:
            return
            
        chat = update.effective_chat
        
        # Only respond in supported chat types
        if chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return
            
        try:
            # Prepare bot information
            bot_username = self.bot_info.username if self.bot_info else "bot"
            group_invite_url = f"https://t.me/{bot_username}?startgroup=true"
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("Updates", url="https://t.me/WorkGlows"),
                    InlineKeyboardButton("Support", url="https://t.me/TheCryptoElders"),
                ],
                [InlineKeyboardButton("Add to Group", url=group_invite_url)],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create welcome message
            welcome_text = (
                f"Group Activity Bot Active\n\n"
                f"What I do:\n"
                f"• Simulate {self.action} actions\n"
                f"• Keep your group active and visible\n"
                f"• Maintain conversation flow\n\n"
                f"Bot is now running in this chat!\n"
                f"Activity simulation will continue automatically."
            )
            
            # Send response
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )
            
            # Start simulation for this chat
            await self.start_chat_simulation(chat.id)
            logger.info(f"Started simulation for chat {chat.id} with {self.action}")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            try:
                await update.message.reply_text("Something went wrong. Please try again.")
            except:
                pass
    
    async def start_chat_simulation(self, chat_id: int):
        """Start action simulation for a specific chat"""
        # Cancel existing simulation if running
        if chat_id in self.active_simulations:
            self.active_simulations[chat_id].cancel()
            try:
                await self.active_simulations[chat_id]
            except asyncio.CancelledError:
                pass
        
        # Start new simulation task
        self.active_simulations[chat_id] = asyncio.create_task(
            self.simulation_loop(chat_id)
        )
    
    async def simulation_loop(self, chat_id: int):
        """Continuous action simulation for a chat"""
        try:
            while not shutdown_event.is_set() and self.is_running:
                try:
                    if self.app and self.app.bot:
                        await self.app.bot.send_chat_action(
                            chat_id=chat_id,
                            action=self.action
                        )
                    
                    # Wait 5 seconds between actions
                    await asyncio.sleep(5.0)
                    
                except (NetworkError, BadRequest) as e:
                    logger.debug(f"API error for chat {chat_id}: {e}")
                    await asyncio.sleep(10.0)
                    
                except Exception as e:
                    logger.debug(f"Simulation error for chat {chat_id}: {e}")
                    await asyncio.sleep(5.0)
                    
        except asyncio.CancelledError:
            logger.info(f"Simulation cancelled for chat {chat_id}")
        except Exception as e:
            logger.error(f"Unexpected error in simulation for chat {chat_id}: {e}")
        finally:
            # Clean up
            if chat_id in self.active_simulations:
                del self.active_simulations[chat_id]
    
    async def start_bot(self):
        """Start the bot and begin polling"""
        try:
            self.is_running = True
            
            # Start application
            await self.app.start()
            
            # Start polling
            await self.app.updater.start_polling(
                poll_interval=2.0,
                timeout=20,
                bootstrap_retries=3,
                read_timeout=20,
                write_timeout=20,
                connect_timeout=20,
                pool_timeout=20,
                drop_pending_updates=True
            )
            
            logger.info(f"Bot polling started for {self.action}")
            
            # Keep running
            while not shutdown_event.is_set() and self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error starting bot for {self.action}: {e}")
        finally:
            await self.stop_bot()
    
    async def stop_bot(self):
        """Stop bot and clean up"""
        try:
            self.is_running = False
            
            # Cancel simulations
            simulation_tasks = list(self.active_simulations.values())
            for task in simulation_tasks:
                task.cancel()
            
            # Wait for completion
            if simulation_tasks:
                await asyncio.gather(*simulation_tasks, return_exceptions=True)
            
            self.active_simulations.clear()
            
            # Stop application
            if self.app:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
            
            logger.info(f"Bot stopped for {self.action}")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for Render health monitoring"""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Calculate statistics
        running_bots = len([bot for bot in bot_instances if bot.is_running])
        total_simulations = sum(len(bot.active_simulations) for bot in bot_instances)
        
        status = (
            f"Telegram Multi-Bot Service\n"
            f"Running bots: {running_bots}/{len(bot_instances)}\n"
            f"Active simulations: {total_simulations}\n"
            f"Configured tokens: {len(BOT_TOKENS)}\n"
            f"Health: {'OK' if running_bots > 0 else 'STARTING'}\n"
        )
        
        self.wfile.write(status.encode())
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        pass


def run_bot_in_thread(token: str, action: ChatAction):
    """Run individual bot in dedicated thread"""
    async def run_bot_async():
        bot = TelegramBot(token, action)
        bot_instances.append(bot)
        
        try:
            if await bot.initialize():
                await bot.start_bot()
        except Exception as e:
            logger.error(f"Critical error in bot thread: {e}")
        finally:
            if bot in bot_instances:
                bot_instances.remove(bot)
    
    # Create event loop for thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_bot_async())
    except Exception as e:
        logger.error(f"Thread error: {e}")
    finally:
        loop.close()


def start_health_server():
    """Start HTTP server for health monitoring"""
    global health_server
    port = int(os.environ.get("PORT", 5000))
    
    try:
        health_server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health server listening on port {port}")
        health_server.serve_forever()
    except Exception as e:
        logger.error(f"Health server error: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down")
    shutdown_event.set()
    
    if health_server:
        health_server.shutdown()
    
    time.sleep(3)
    sys.exit(0)


def main():
    """Main application entry point"""
    logger.info("=== Telegram Multi-Bot Service ===")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Bot tokens: {len(BOT_TOKENS)}")
    logger.info(f"Available actions: {len(CHAT_ACTIONS)}")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start health server
        health_thread = threading.Thread(
            target=start_health_server,
            daemon=True,
            name="HealthServer"
        )
        health_thread.start()
        logger.info("Health server started")
        
        # Start bot threads
        bot_threads = []
        tokens_to_use = BOT_TOKENS[:len(CHAT_ACTIONS)]
        actions_to_use = CHAT_ACTIONS[:len(tokens_to_use)]
        
        for i, (token, action) in enumerate(zip(tokens_to_use, actions_to_use)):
            # Stagger starts
            if i > 0:
                time.sleep(3)
            
            thread = threading.Thread(
                target=run_bot_in_thread,
                args=(token, action),
                daemon=True,
                name=f"Bot-{action}"
            )
            bot_threads.append(thread)
            thread.start()
            logger.info(f"Started bot thread for {action}")
        
        logger.info(f"All {len(bot_threads)} bots started")
        
        # Main loop
        while not shutdown_event.is_set():
            time.sleep(1)
            
            # Monitor threads
            alive_threads = [t for t in bot_threads if t.is_alive()]
            if len(alive_threads) < len(bot_threads):
                logger.warning(f"Thread health: {len(alive_threads)}/{len(bot_threads)} alive")
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    finally:
        logger.info("Shutting down")
        shutdown_event.set()
        
        if health_server:
            health_server.shutdown()
        
        time.sleep(2)
        logger.info("Shutdown complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())