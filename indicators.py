import asyncio
import os
import logging
import signal
import sys
import threading
import random
from typing import Dict, List, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import telegram components
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Bot as TelegramBot
    from telegram.constants import ChatAction, ChatType
    from telegram.error import NetworkError, BadRequest, TelegramError
    logger.info("Telegram imports successful")
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

# Reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Configuration
BOT_TOKENS = os.getenv("BOT_TOKENS", "").split(",")
if not BOT_TOKENS or BOT_TOKENS == [""]:
    logger.error("BOT_TOKENS environment variable required")
    sys.exit(1)

BOT_TOKENS = [token.strip() for token in BOT_TOKENS if token.strip()]
if not BOT_TOKENS:
    logger.error("No valid tokens")
    sys.exit(1)

# Actions
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

# Action display names
ACTION_DISPLAY_NAMES = {
    ChatAction.TYPING: "Typing",
    ChatAction.UPLOAD_PHOTO: "Uploading Photo",
    ChatAction.RECORD_VIDEO: "Recording Video",
    ChatAction.UPLOAD_VIDEO: "Uploading Video",
    ChatAction.RECORD_VOICE: "Recording Voice",
    ChatAction.UPLOAD_VOICE: "Uploading Voice",
    ChatAction.UPLOAD_DOCUMENT: "Uploading Document",
    ChatAction.CHOOSE_STICKER: "Choosing Sticker",
    ChatAction.FIND_LOCATION: "Finding Location",
    ChatAction.RECORD_VIDEO_NOTE: "Recording Video Note",
    ChatAction.UPLOAD_VIDEO_NOTE: "Uploading Video Note",
}

# Random photos for start command
RANDOM_PHOTOS = [
    "https://i.postimg.cc/RhtZR0sF/New-Project-235-28-ED42-B.png",
    "https://i.postimg.cc/k4z5KSyz/New-Project-235-8-AFAF2-A.png",
    "https://i.postimg.cc/N0NFGS2g/New-Project-235-09-DD635.png",
    "https://i.postimg.cc/6pfTgy94/New-Project-235-3-D5-D3-F1.png",
    "https://i.postimg.cc/dVYL58KK/New-Project-235-4235-F6-E.png",
    "https://i.postimg.cc/tCPsdBw5/New-Project-235-3459944.png",
    "https://i.postimg.cc/8k7Jcpbx/New-Project-235-3079612.png",
    "https://i.postimg.cc/MXk8KbYZ/New-Project-235-9-A5-CAF0.png",
    "https://i.postimg.cc/qRRrm7Rr/New-Project-235-FE6-E983.png",
    "https://i.postimg.cc/zfp5Shqp/New-Project-235-5-B71865.png",
    "https://i.postimg.cc/BvJ4KpfX/New-Project-235-739-D6-D5.png",
    "https://i.postimg.cc/t439JffK/New-Project-235-B98-C0-D6.png",
    "https://i.postimg.cc/pLb22x0Q/New-Project-235-28-F28-CA.png",
    "https://i.postimg.cc/MHgzf8zS/New-Project-235-AB8-F78-F.png",
    "https://i.postimg.cc/wvfqHmP3/New-Project-235-5952549.png",
    "https://i.postimg.cc/mrSZXqyY/New-Project-235-D231974.png",
    "https://i.postimg.cc/vmyHvMf8/New-Project-235-0-BC9-C74.png",
    "https://i.postimg.cc/J4ynrpR8/New-Project-235-88-BC2-D0.png",
    "https://i.postimg.cc/HnNk0y4F/New-Project-235-7462142.png",
    "https://i.postimg.cc/tT2TTf1q/New-Project-235-CE958-B1.png",
    "https://i.postimg.cc/Xv6XD9Sb/New-Project-235-0-E24-C88.png",
    "https://i.postimg.cc/RhpNP89s/New-Project-235-FC3-A4-AD.png",
    "https://i.postimg.cc/x841BwFW/New-Project-235-FFA9646.png",
    "https://i.postimg.cc/5NC7HwSV/New-Project-235-A06-DD7-A.png",
    "https://i.postimg.cc/HnPqpdm9/New-Project-235-9-E45-B87.png",
    "https://i.postimg.cc/1tSPTmRg/New-Project-235-AB394-C0.png",
    "https://i.postimg.cc/8ct1M2S7/New-Project-235-9-CAE309.png",
    "https://i.postimg.cc/TYtwDDdt/New-Project-235-2-F658-B0.png",
    "https://i.postimg.cc/xdwqdVfY/New-Project-235-68-BAF06.png",
    "https://i.postimg.cc/hPczxn9t/New-Project-235-9-E9-A004.png",
    "https://i.postimg.cc/jjFPQ1Rk/New-Project-235-A1-E7-CC1.png",
    "https://i.postimg.cc/TPqJV0pz/New-Project-235-CA65155.png",
    "https://i.postimg.cc/wBh0WHbb/New-Project-235-89799-CD.png",
    "https://i.postimg.cc/FKdQ1fzk/New-Project-235-C377613.png",
    "https://i.postimg.cc/rpKqWnnm/New-Project-235-CFD2548.png",
    "https://i.postimg.cc/g0kn7HMF/New-Project-235-C4-A32-AC.png",
    "https://i.postimg.cc/XY6jRkY1/New-Project-235-28-DCBC9.png",
    "https://i.postimg.cc/SN32J9Nc/New-Project-235-99-D1478.png",
    "https://i.postimg.cc/8C86n62T/New-Project-235-F1556-B9.png",
    "https://i.postimg.cc/RCGwVqHT/New-Project-235-5-BBB339.png",
    "https://i.postimg.cc/pTfYBZyN/New-Project-235-17-D796-A.png",
    "https://i.postimg.cc/zGgdgJJc/New-Project-235-165-FE5-A.png"
]

# Global state
active_bots = []
shutdown_signal = threading.Event()
http_server = None


class BotInstance:
    """Bot with direct polling"""

    def __init__(self, token: str, action: ChatAction):
        self.token = token
        self.action = action
        self.bot = TelegramBot(token)
        self.simulations = {}
        self.running = False
        self.bot_info = None
        self.offset = 0

    async def initialize(self):
        """Initialize bot"""
        try:
            self.bot_info = await self.bot.get_me()
            commands = [
                BotCommand("start", "Start activity simulation"),
                BotCommand("end", "Stop activity simulation")
            ]
            await self.bot.set_my_commands(commands)
            logger.info(f"Bot @{self.bot_info.username} initialized for {self.action}")
            return True
        except Exception as e:
            logger.error(f"Initialize error for {self.action}: {e}")
            return False

    async def handle_update(self, update_data: dict):
        """Handle incoming update"""
        try:
            update = Update.de_json(update_data, self.bot)
            if not update or not update.message:
                return

            message = update.message
            if not message.text:
                return

            chat = message.chat
            if chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
                return

            # Handle /start command
            if message.text.startswith('/start'):
                await self.handle_start_command(chat, message.from_user)
            
            # Handle /end command
            elif message.text.startswith('/end'):
                await self.handle_end_command(chat, message.from_user)
                
            # Handle /ping command (hidden from menu)
            elif message.text.startswith('/ping'):
                await self.handle_ping_command(chat, message.from_user)

        except Exception as e:
            logger.error(f"Handle update error: {e}")

    async def handle_start_command(self, chat, user):
        """Handle /start command"""
        try:
            # Select a random photo
            random_photo = random.choice(RANDOM_PHOTOS)
            
            # Construct the "Add Me To Your Group" URL
            username = self.bot_info.username if self.bot_info else "bot"
            add_to_group_url = f"https://t.me/{username}?startgroup=true"

            # Build the keyboard with updated button text
            keyboard = [
                [
                    InlineKeyboardButton(text="Updates", url="https://t.me/WorkGlows"),
                    InlineKeyboardButton(text="Support", url="https://t.me/SoulMeetsHQ"),
                ],
                [
                    InlineKeyboardButton(
                        text="Add Me To Your Group",
                        url=add_to_group_url,
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Prepare user mention via HTML link
            # Use first_name if available, otherwise username or fallback text
            if user.first_name:
                display_name = user.first_name
            elif user.username:
                display_name = f"@{user.username}"
            else:
                display_name = "there"
            user_mention = f'<a href="tg://user?id={user.id}">{display_name}</a>'

            # Rich welcome text with emojis, HTML formatting, and user mention
            action_display = ACTION_DISPLAY_NAMES.get(self.action, str(self.action))
            welcome_text = f"""
👋 Hello {user_mention}, welcome!

I display fun activity indicators in groups and private chats! 💘

<blockquote>⚙️ Now Simulating: {action_display}</blockquote>

💬 <i>Press /end to stop the simulation!</i>
"""

            # Send the photo with caption and keyboard
            await self.bot.send_photo(
                chat_id=chat.id,
                photo=random_photo,
                caption=welcome_text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

            # Start simulation if not already running
            await self.start_simulation(chat.id)
            logger.info(f"Simulation started for chat {chat.id}")

        except Exception as e:
            logger.error(f"Start command error: {e}")
            # Fallback to text message if photo fails
            try:
                welcome_text = f"""
👋 Hello {user_mention}, welcome!

I display fun activity indicators in groups and private chats. Use the buttons below for help or to add me to your group! 💘

<blockquote>⚙️ Now Simulating: {action_display}</blockquote>

💬 Press /end to stop the simulation
"""
                
                await self.bot.send_message(
                    chat_id=chat.id,
                    text=welcome_text,
                    parse_mode="HTML"
                )
                
                await self.start_simulation(chat.id)
            except Exception as fallback_error:
                logger.error(f"Fallback message error: {fallback_error}")

    async def handle_end_command(self, chat, user):
        """Handle /end command"""
        try:
            # Prepare user mention
            if user.first_name:
                display_name = user.first_name
            elif user.username:
                display_name = f"@{user.username}"
            else:
                display_name = "there"
            user_mention = f'<a href="tg://user?id={user.id}">{display_name}</a>'

            # Stop simulation for this chat
            simulation_stopped = await self.stop_simulation(chat.id)

            if simulation_stopped:
                end_text = f"""
Ok {user_mention}, simulation stopped! 💫

The activity indicators have been turned off for now. 💡

<blockquote>✨ Simulation Disabled: {self.action}</blockquote>

💕 Just use /start anytime to resume!
"""
            else:
                end_text = f"""
{user_mention}, no active simulation found to stop. 💫

There was nothing running to disable right now. 💡

<blockquote>✨ No simulation active</blockquote>

💕 Use /start to begin anytime!
"""

            await self.bot.send_message(
                chat_id=chat.id,
                text=end_text,
                parse_mode="HTML"
            )

            logger.info(f"End command processed for chat {chat.id}, stopped: {simulation_stopped}")

        except Exception as e:
            logger.error(f"End command error: {e}")

    async def handle_ping_command(self, chat, user):
        """Handle /ping command (hidden from menu)"""
        try:
            start_time = time.time()
            
            # Send initial ping message
            ping_message = await self.bot.send_message(
                chat_id=chat.id,
                text="🛰️ Pinging...",
                parse_mode="HTML"
            )
            
            # Calculate response time
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            
            # Update message with actual ping
            ping_text = f'🏓 <a href="https://t.me/SoulMeetsHQ">Pong!</a> {response_time}ms'
            
            await self.bot.edit_message_text(
                chat_id=chat.id,
                message_id=ping_message.message_id,
                text=ping_text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
            logger.info(f"Ping command processed for chat {chat.id}, response time: {response_time}ms")

        except Exception as e:
            logger.error(f"Ping command error: {e}")

    async def start_simulation(self, chat_id: int):
        """Start simulation"""
        if chat_id in self.simulations:
            self.simulations[chat_id].cancel()

        self.simulations[chat_id] = asyncio.create_task(
            self.simulate_loop(chat_id)
        )

    async def stop_simulation(self, chat_id: int) -> bool:
        """Stop simulation for a specific chat"""
        if chat_id in self.simulations:
            self.simulations[chat_id].cancel()
            self.simulations.pop(chat_id, None)
            return True
        return False

    async def simulate_loop(self, chat_id: int):
        """Simulation loop"""
        try:
            while not shutdown_signal.is_set() and self.running:
                try:
                    await self.bot.send_chat_action(chat_id, self.action)
                    await asyncio.sleep(5.0)
                except (NetworkError, BadRequest):
                    await asyncio.sleep(10.0)
                except Exception:
                    await asyncio.sleep(5.0)
        except asyncio.CancelledError:
            pass
        finally:
            self.simulations.pop(chat_id, None)

    async def poll_updates(self):
        """Direct polling for updates"""
        while not shutdown_signal.is_set() and self.running:
            try:
                updates = await self.bot.get_updates(
                    offset=self.offset,
                    timeout=10,
                    limit=100
                )

                for update in updates:
                    self.offset = update.update_id + 1
                    await self.handle_update(update.to_dict())

                if not updates:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.debug(f"Poll error for {self.action}: {e}")
                await asyncio.sleep(5)

    async def run(self):
        """Run bot"""
        try:
            self.running = True
            logger.info(f"Bot started for {self.action}")
            await self.poll_updates()
        except Exception as e:
            logger.error(f"Run error for {self.action}: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup"""
        try:
            self.running = False

            # Cancel simulations
            for task in list(self.simulations.values()):
                task.cancel()

            if self.simulations:
                await asyncio.gather(*self.simulations.values(), return_exceptions=True)

            logger.info(f"Bot cleaned up for {self.action}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


def run_bot_thread(token: str, action: ChatAction):
    """Run bot in thread"""
    async def bot_main():
        bot = BotInstance(token, action)
        active_bots.append(bot)

        try:
            if await bot.initialize():
                await bot.run()
        except Exception as e:
            logger.error(f"Bot thread error: {e}")
        finally:
            if bot in active_bots:
                active_bots.remove(bot)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(bot_main())
    except Exception as e:
        logger.error(f"Thread error: {e}")
    finally:
        loop.close()


class HealthHandler(BaseHTTPRequestHandler):
    """Health check handler"""

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        running = len([b for b in active_bots if b.running])
        sims = sum(len(b.simulations) for b in active_bots)

        status = (
            f"Telegram Multi-Bot Service\n"
            f"Running: {running}/{len(active_bots)}\n"
            f"Simulations: {sims}\n"
            f"Tokens: {len(BOT_TOKENS)}\n"
            f"Status: OK\n"
        )

        self.wfile.write(status.encode())

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def start_server():
    """Start HTTP server"""
    global http_server
    port = int(os.environ.get("PORT", 5000))

    try:
        http_server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info(f"Server on port {port}")
        http_server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")


def signal_handler(signum, frame):
    """Handle signals"""
    logger.info("Shutting down")
    shutdown_signal.set()

    if http_server:
        http_server.shutdown()

    time.sleep(2)
    sys.exit(0)


def main():
    """Main function"""
    logger.info("=== Telegram Multi-Bot Service ===")
    logger.info(f"Tokens: {len(BOT_TOKENS)}")
    logger.info(f"Actions: {len(ACTIONS)}")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start server
        server_thread = threading.Thread(
            target=start_server,
            daemon=True
        )
        server_thread.start()

        # Start bots
        threads = []
        tokens = BOT_TOKENS[:len(ACTIONS)]
        actions = ACTIONS[:len(tokens)]

        for i, (token, action) in enumerate(zip(tokens, actions)):
            if i > 0:
                time.sleep(2)

            thread = threading.Thread(
                target=run_bot_thread,
                args=(token, action),
                daemon=True
            )
            threads.append(thread)
            thread.start()
            logger.info(f"Started {action}")

        logger.info(f"All {len(threads)} bots started")

        # Keep running
        while not shutdown_signal.is_set():
            time.sleep(1)

    except Exception as e:
        logger.error(f"Main error: {e}")
        return 1
    finally:
        shutdown_signal.set()
        if http_server:
            http_server.shutdown()
        time.sleep(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())