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

### 💌 Connect with Me

<p align="center">
  <a href="https://t.me/asad_ofc"><img src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" /></a>
  <a href="mailto:mr.asadul.islam00@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white" /></a>
  <a href="https://youtube.com/@asad_ofc"><img src="https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" /></a>
  <a href="https://instagram.com/aasad_ofc"><img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" /></a>
  <a href="https://tiktok.com/@asad_ofc"><img src="https://img.shields.io/badge/TikTok-000000?style=for-the-badge&logo=tiktok&logoColor=white" /></a>
  <a href="https://x.com/asad_ofc"><img src="https://img.shields.io/badge/X-000000?style=for-the-badge&logo=twitter&logoColor=white" /></a>
  <a href="https://facebook.com/aasad.ofc"><img src="https://img.shields.io/badge/Facebook-1877F2?style=for-the-badge&logo=facebook&logoColor=white" /></a>
  <a href="https://www.threads.net/@aasad_ofc"><img src="https://img.shields.io/badge/Threads-000000?style=for-the-badge&logo=threads&logoColor=white" /></a>
  <a href="https://discord.com/users/1067999831416635473"><img src="https://img.shields.io/badge/Discord-asad__ofc-5865F2?style=for-the-badge&logo=discord&logoColor=white" /></a>
</p>

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
