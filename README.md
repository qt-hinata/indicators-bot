# 🤖 ChatAction Simulator Bot — Keep Your Telegram Presence Alive  
[![Telegram Bot](https://img.shields.io/badge/Launch%20Bot-@WorkGlows-2CA5E0?logo=telegram&style=for-the-badge)](https://t.me/WorkGlows)
> **Real-time. Reactive. Silent.**  
> This bot mimics user activity like "typing...", "uploading photo...", and more whenever someone texts your bot — perfect for faking presence, demoing, or trolling.

---

## ✨ What It Does

- 🔄 Sends continuous `ChatAction` (like typing, uploading, recording, etc.) in chats where someone sends a message  
- 🤹 Supports **multiple bots at once** (via comma-separated tokens)  
- 🧠 Works in **private chats**, **groups**, and **supergroups**  
- ⚙️ Fully async — scales well and is low-resource  
- 🔒 Zero user interaction — runs silently in the background  

---

## 💬 Chat Actions It Can Simulate

| Action               | Visual Effect in Telegram         |
|----------------------|-----------------------------------|
| `typing`             | Shows “typing…”                   |
| `upload_photo`       | Shows “uploading photo…”          |
| `record_video`       | Shows “recording video…”          |
| `upload_video`       | Shows “uploading video…”          |
| `record_voice`       | Shows “recording voice message…”  |
| `upload_voice`       | Shows “uploading voice message…”  |
| `upload_document`    | Shows “uploading document…”       |
| `choose_sticker`     | Shows “choosing sticker…”         |
| `find_location`      | Shows “finding location…”         |
| `record_video_note`  | Shows “recording video note…”     |
| `upload_video_note`  | Shows “uploading video note…”     |

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+  
- **Framework:** [python-telegram-bot v20+](https://github.com/python-telegram-bot/python-telegram-bot)  
- **Concurrency:** `asyncio`  
- **Hosting:** Compatible with any Python-supporting environment  

---

## 🚀 How to Run

```bash
# 1. Clone the repo
git clone https://github.com/your-username/chat-action-simulator-bot.git
cd chat-action-simulator-bot

# 2. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate

# 3. Install required packages
pip install -r requirements.txt

# 4. Set your bot tokens (comma-separated if multiple)
export BOT_TOKENS="123456:ABC-DEF1234ghIkl,987654:XYZ-321abcDEF"

# 5. Run the bot
python bot.py
