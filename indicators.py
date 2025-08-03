import os
import sys
import time
import json
import signal
import random
import asyncio
import logging
import threading
from typing import Dict, List, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import (
    Bot as TelegramBot,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction, ChatType
from telegram.error import BadRequest, NetworkError, TelegramError

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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

UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "https://t.me/WorkGlows")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/SoulMeetsHQ")

# Bot actions
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

# Bot commands
BOT_COMMANDS = [
    BotCommand("start", "Start activity simulation"),
    BotCommand("end", "Stop activity simulation")
]

# Random photos for start command
RANDOM_PHOTOS = [
    "https://ik.imagekit.io/asadofc/Images1.png",
    "https://ik.imagekit.io/asadofc/Images2.png",
    "https://ik.imagekit.io/asadofc/Images3.png",
    "https://ik.imagekit.io/asadofc/Images4.png",
    "https://ik.imagekit.io/asadofc/Images5.png",
    "https://ik.imagekit.io/asadofc/Images6.png",
    "https://ik.imagekit.io/asadofc/Images7.png",
    "https://ik.imagekit.io/asadofc/Images8.png",
    "https://ik.imagekit.io/asadofc/Images9.png",
    "https://ik.imagekit.io/asadofc/Images10.png",
    "https://ik.imagekit.io/asadofc/Images11.png",
    "https://ik.imagekit.io/asadofc/Images12.png",
    "https://ik.imagekit.io/asadofc/Images13.png",
    "https://ik.imagekit.io/asadofc/Images14.png",
    "https://ik.imagekit.io/asadofc/Images15.png",
    "https://ik.imagekit.io/asadofc/Images16.png",
    "https://ik.imagekit.io/asadofc/Images17.png",
    "https://ik.imagekit.io/asadofc/Images18.png",
    "https://ik.imagekit.io/asadofc/Images19.png",
    "https://ik.imagekit.io/asadofc/Images20.png",
    "https://ik.imagekit.io/asadofc/Images21.png",
    "https://ik.imagekit.io/asadofc/Images22.png",
    "https://ik.imagekit.io/asadofc/Images23.png",
    "https://ik.imagekit.io/asadofc/Images24.png",
    "https://ik.imagekit.io/asadofc/Images25.png",
    "https://ik.imagekit.io/asadofc/Images26.png",
    "https://ik.imagekit.io/asadofc/Images27.png",
    "https://ik.imagekit.io/asadofc/Images28.png",
    "https://ik.imagekit.io/asadofc/Images29.png",
    "https://ik.imagekit.io/asadofc/Images30.png",
    "https://ik.imagekit.io/asadofc/Images31.png",
    "https://ik.imagekit.io/asadofc/Images32.png",
    "https://ik.imagekit.io/asadofc/Images33.png",
    "https://ik.imagekit.io/asadofc/Images34.png",
    "https://ik.imagekit.io/asadofc/Images35.png",
    "https://ik.imagekit.io/asadofc/Images36.png",
    "https://ik.imagekit.io/asadofc/Images37.png",
    "https://ik.imagekit.io/asadofc/Images38.png",
    "https://ik.imagekit.io/asadofc/Images39.png",
    "https://ik.imagekit.io/asadofc/Images40.png"
]

# Message templates
WELCOME_MESSAGE = """
👋 Hello {user_mention}, welcome!

I display fun activity indicators in groups and private chats! 💘

<blockquote>⚙️ Now Simulating: {action_display}</blockquote>

💬 <i>Press /end to stop the simulation!</i>
"""

END_MESSAGE_STOPPED = """
Ok {user_mention}, simulation stopped! 💫

The activity indicators have been turned off for now. 💡

<blockquote>✨ Simulation Disabled: {action}</blockquote>

💕 Just use /start anytime to resume!
"""

END_MESSAGE_NOT_RUNNING = """
{user_mention}, no active simulation found to stop. 💫

There was nothing running to disable right now. 💡

<blockquote>✨ No simulation active</blockquote>

💕 Use /start to begin anytime!
"""

PING_INITIAL = "🛰️ Pinging..."
PING_RESPONSE = '🏓 <a href="{support_url}">Pong!</a> {response_time}ms'

FALLBACK_WELCOME = """
👋 Hello {user_mention}, welcome!

I display fun activity indicators in groups and private chats. Use the buttons below for help or to add me to your group! 💘

<blockquote>⚙️ Now Simulating: {action_display}</blockquote>

💬 Press /end to stop the simulation
"""

# Global state
active_bots = []
shutdown_signal = threading.Event()
http_server = None

# Bot data structure
bot_instances = {}


def get_user_mention(user):
    if user.first_name:
        display_name = user.first_name
    elif user.username:
        display_name = f"@{user.username}"
    else:
        display_name = "there"
    return f'<a href="tg://user?id={user.id}">{display_name}</a>'


async def initialize_bot(token: str, action: ChatAction):
    try:
        bot = TelegramBot(token)
        bot_info = await bot.get_me()
        await bot.set_my_commands(BOT_COMMANDS)
        
        bot_data = {
            'bot': bot,
            'action': action,
            'simulations': {},
            'running': False,
            'bot_info': bot_info,
            'offset': 0
        }
        
        bot_instances[token] = bot_data
        logger.info(f"Bot @{bot_info.username} initialized for {action}")
        return True
    except Exception as e:
        logger.error(f"Initialize error for {action}: {e}")
        return False


async def handle_update(token: str, update_data: dict):
    try:
        bot_data = bot_instances[token]
        bot = bot_data['bot']
        action = bot_data['action']
        
        update = Update.de_json(update_data, bot)
        if not update or not update.message:
            return

        message = update.message
        if not message.text:
            return

        chat = message.chat
        if chat.type not in [ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]:
            return

        if message.text.startswith('/start'):
            await handle_start_command(token, chat, message.from_user)
        elif message.text.startswith('/end'):
            await handle_end_command(token, chat, message.from_user)
        elif message.text.startswith('/ping'):
            await handle_ping_command(token, chat, message.from_user, message)

    except Exception as e:
        logger.error(f"Handle update error: {e}")


async def handle_start_command(token: str, chat, user):
    try:
        bot_data = bot_instances[token]
        bot = bot_data['bot']
        action = bot_data['action']
        bot_info = bot_data['bot_info']
        
        random_photo = random.choice(RANDOM_PHOTOS)
        username = bot_info.username if bot_info else "bot"
        add_to_group_url = f"https://t.me/{username}?startgroup=true"

        keyboard = [
            [
                InlineKeyboardButton(text="Updates", url=UPDATE_CHANNEL),
                InlineKeyboardButton(text="Support", url=SUPPORT_CHANNEL),
            ],
            [
                InlineKeyboardButton(
                    text="Add Me To Your Group",
                    url=add_to_group_url,
                ),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        user_mention = get_user_mention(user)
        action_display = ACTION_DISPLAY_NAMES.get(action, str(action))
        
        welcome_text = WELCOME_MESSAGE.format(
            user_mention=user_mention,
            action_display=action_display
        )

        await bot.send_photo(
            chat_id=chat.id,
            photo=random_photo,
            caption=welcome_text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        await start_simulation(token, chat.id)
        logger.info(f"Simulation started for chat {chat.id}")

    except Exception as e:
        logger.error(f"Start command error: {e}")
        await send_fallback_welcome(token, chat, user)


async def send_fallback_welcome(token: str, chat, user):
    try:
        bot_data = bot_instances[token]
        bot = bot_data['bot']
        action = bot_data['action']
        
        user_mention = get_user_mention(user)
        action_display = ACTION_DISPLAY_NAMES.get(action, str(action))
        
        fallback_text = FALLBACK_WELCOME.format(
            user_mention=user_mention,
            action_display=action_display
        )
        
        await bot.send_message(
            chat_id=chat.id,
            text=fallback_text,
            parse_mode="HTML"
        )
        
        await start_simulation(token, chat.id)
    except Exception as fallback_error:
        logger.error(f"Fallback message error: {fallback_error}")


async def handle_end_command(token: str, chat, user):
    try:
        bot_data = bot_instances[token]
        bot = bot_data['bot']
        action = bot_data['action']
        
        user_mention = get_user_mention(user)
        simulation_stopped = await stop_simulation(token, chat.id)

        if simulation_stopped:
            end_text = END_MESSAGE_STOPPED.format(
                user_mention=user_mention,
                action=action
            )
        else:
            end_text = END_MESSAGE_NOT_RUNNING.format(
                user_mention=user_mention
            )

        await bot.send_message(
            chat_id=chat.id,
            text=end_text,
            parse_mode="HTML"
        )

        logger.info(f"End command processed for chat {chat.id}, stopped: {simulation_stopped}")

    except Exception as e:
        logger.error(f"End command error: {e}")


async def handle_ping_command(token: str, chat, user, message):
    try:
        bot_data = bot_instances[token]
        bot = bot_data['bot']
        
        start_time = time.time()
        
        # In groups reply to message, in private just send
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            ping_message = await bot.send_message(
                chat_id=chat.id,
                text=PING_INITIAL,
                reply_to_message_id=message.message_id,
                parse_mode="HTML"
            )
        else:
            ping_message = await bot.send_message(
                chat_id=chat.id,
                text=PING_INITIAL,
                parse_mode="HTML"
            )
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        ping_text = PING_RESPONSE.format(
            support_url=SUPPORT_CHANNEL,
            response_time=response_time
        )
        
        await bot.edit_message_text(
            chat_id=chat.id,
            message_id=ping_message.message_id,
            text=ping_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        logger.info(f"Ping command processed for chat {chat.id}, response time: {response_time}ms")

    except Exception as e:
        logger.error(f"Ping command error: {e}")


async def start_simulation(token: str, chat_id: int):
    bot_data = bot_instances[token]
    simulations = bot_data['simulations']
    
    if chat_id in simulations:
        simulations[chat_id].cancel()

    simulations[chat_id] = asyncio.create_task(
        simulate_loop(token, chat_id)
    )


async def stop_simulation(token: str, chat_id: int) -> bool:
    bot_data = bot_instances[token]
    simulations = bot_data['simulations']
    
    if chat_id in simulations:
        simulations[chat_id].cancel()
        simulations.pop(chat_id, None)
        return True
    return False


async def simulate_loop(token: str, chat_id: int):
    try:
        bot_data = bot_instances[token]
        bot = bot_data['bot']
        action = bot_data['action']
        
        while not shutdown_signal.is_set() and bot_data['running']:
            try:
                await bot.send_chat_action(chat_id, action)
                await asyncio.sleep(5.0)
            except (NetworkError, BadRequest):
                await asyncio.sleep(10.0)
            except Exception:
                await asyncio.sleep(5.0)
    except asyncio.CancelledError:
        pass
    finally:
        bot_data['simulations'].pop(chat_id, None)


async def poll_updates(token: str):
    bot_data = bot_instances[token]
    bot = bot_data['bot']
    action = bot_data['action']
    
    while not shutdown_signal.is_set() and bot_data['running']:
        try:
            updates = await bot.get_updates(
                offset=bot_data['offset'],
                timeout=10,
                limit=100
            )

            for update in updates:
                bot_data['offset'] = update.update_id + 1
                await handle_update(token, update.to_dict())

            if not updates:
                await asyncio.sleep(1)

        except Exception as e:
            logger.debug(f"Poll error for {action}: {e}")
            await asyncio.sleep(5)


async def run_bot(token: str, action: ChatAction):
    try:
        bot_instances[token]['running'] = True
        logger.info(f"Bot started for {action}")
        await poll_updates(token)
    except Exception as e:
        logger.error(f"Run error for {action}: {e}")
    finally:
        await cleanup_bot(token)


async def cleanup_bot(token: str):
    try:
        if token not in bot_instances:
            return
            
        bot_data = bot_instances[token]
        bot_data['running'] = False
        simulations = bot_data['simulations']

        # Cancel all simulations
        for task in list(simulations.values()):
            task.cancel()

        if simulations:
            await asyncio.gather(*simulations.values(), return_exceptions=True)

        logger.info(f"Bot cleaned up for {bot_data['action']}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def run_bot_thread(token: str, action: ChatAction):
    async def bot_main():
        try:
            if await initialize_bot(token, action):
                await run_bot(token, action)
        except Exception as e:
            logger.error(f"Bot thread error: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(bot_main())
    except Exception as e:
        logger.error(f"Thread error: {e}")
    finally:
        loop.close()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        running = len([b for b in bot_instances.values() if b['running']])
        sims = sum(len(b['simulations']) for b in bot_instances.values())

        status = (
            f"Telegram Multi-Bot Service\n"
            f"Running: {running}/{len(bot_instances)}\n"
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
    global http_server
    port = int(os.environ.get("PORT", 5000))

    try:
        http_server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info(f"Server on port {port}")
        http_server.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")


def signal_handler(signum, frame):
    logger.info("Shutting down")
    shutdown_signal.set()

    if http_server:
        http_server.shutdown()

    time.sleep(2)
    sys.exit(0)


def main():
    logger.info("=== Telegram Multi-Bot Service ===")
    logger.info(f"Tokens: {len(BOT_TOKENS)}")
    logger.info(f"Actions: {len(ACTIONS)}")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        server_thread = threading.Thread(
            target=start_server,
            daemon=True
        )
        server_thread.start()

        # Start bot threads
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

        # Keep service running
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