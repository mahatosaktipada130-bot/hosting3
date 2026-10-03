# ====================================================
#          👑  Rᴜsʜᴇʀ Kɪɴɢ  👑  •  👑  Rᴜsʜᴇʀ Kɪɴɢ  👑 HOSTING v5.2 (Free Edition)
# ====================================================

import os
import sys
import sqlite3
import subprocess
import time
import random
import string
import threading
import re
import signal
import html as html_mod
from datetime import datetime, timedelta
from telebot import TeleBot, types
from flask import Flask

# ==================== WEB SERVER (FLASK) ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()

# ==================== CONFIG ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "0")
OWNER_NAME = "👑  Rᴜsʜᴇʀ Kɪɴɢ  👑"

HOST_DIR = "hosted_files"
MAX_LOG_SIZE_MB = 5

DEFAULT_EMOJI = {
    "fire": "5424972470023104089",
    "star": "5438496463044752972",
    "check": "5206607081334906820",
    "cross": "5210952531676504517",
    "bell": "5458603043203327669",
    "money": "5409048419211682843",
    "lock": "5296369303661067030",
    "warning": "5447644880824181073",
    "settings": "5341715473882955310",
    "gift": "5309849913218071967",
    "rocket": "5188481279963715781",
    "diamond": "5199448307155350272",
    "wave": "5870734657384877785",
    "user": "5879770735999717115",
    "people": "5942877472163892475",
    "bot": "5931415565955503486",
    "link": "5271604874419647061",
    "refresh": "5375338737028841420",
    "top": "5415655814079723871",
    "card": "5927169041595634481",
    "support": "5884510167986343350",
    "urgent": "5224607267797606837",
    "crown": "5438496463044752972",
    "spark": "5424972470023104089",
}

config = {
    "brand_name": "👑 RUSHER KING 👑",
    "free_limit": "Unlimited",
    "channel_username": "",
    "admin_username": "",
    "bot_username": "rkhosting3bot"
}
EMOJI_IDS = dict(DEFAULT_EMOJI)

os.makedirs(HOST_DIR, exist_ok=True)
bot = TeleBot(BOT_TOKEN, threaded=True, num_threads=50)

# ==================== DATABASE ====================
def get_db():
    conn = sqlite3.connect("hosting_data.db", check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hosted_bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            filepath TEXT,
            logpath TEXT,
            pid INTEGER DEFAULT NULL,
            status TEXT DEFAULT 'stopped',
            auto_guard INTEGER DEFAULT 1,
            created_at TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def ce(emoji_id: str, fallback: str) -> str:
    if emoji_id and str(emoji_id).isdigit():
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback

def pe(key: str, fallback: str) -> str:
    eid = EMOJI_IDS.get(key) or DEFAULT_EMOJI.get(key)
    return ce(str(eid), fallback) if eid else fallback

def brand() -> str:
    return config.get("brand_name") or "👑 RUSHER KING 👑"

# ==================== HELPERS ====================
def register_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    conn.close()

def send_typing(chat_id):
    try:
        bot.send_chat_action(chat_id, 'typing')
    except Exception:
        pass

def send_or_edit(chat_id, text, reply_markup=None, message_id=None, parse_mode="HTML"):
    send_typing(chat_id)
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode=parse_mode, reply_markup=reply_markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup)

def is_process_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def safe_popen(filepath, logpath):
    log_file = open(logpath, 'a', encoding='utf-8')
    log_file.write(f"\n--- [STARTED {datetime.now()}] ---\n")
    log_file.flush()
    cmd = [sys.executable, "-u", filepath]
    cwd = os.path.dirname(filepath) or "."
    try:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, cwd=cwd, start_new_session=True)
    except Exception:
        try:
            log_file.close()
        except Exception:
            pass
        log_file = open(logpath, 'a', encoding='utf-8')
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, cwd=cwd)
    return proc

def safe_kill(pid):
    if not pid or not is_process_alive(pid):
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        time.sleep(0.3)
        if is_process_alive(pid):
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.3)
            if is_process_alive(pid):
                os.kill(pid, 9)
        except Exception:
            try:
                os.kill(pid, 9)
            except Exception:
                pass

# ==================== AUTO LIBRARY INSTALLER ====================
def extract_imports(filepath):
    packages = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        for match in re.finditer(r'^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)', content, re.MULTILINE):
            pkg = match.group(1).split('.')[0]
            stdlib = {'os', 'sys', 'time', 'datetime', 'json', 're', 'math', 'random', 'string', 'threading', 'subprocess', 'sqlite3', 'logging', 'collections', 'functools', 'itertools', 'pathlib', 'shutil', 'tempfile', 'urllib', 'http', 'socket', 'ssl', 'hashlib', 'base64', 'pickle', 'copy', 'traceback', 'typing', 'enum', 'abc', 'io', 'csv', 'xml', 'html', 'email', 'asyncio', 'queue', 'signal', 'platform'}
            if pkg and pkg not in stdlib and not pkg.startswith('_'):
                packages.add(pkg)
    except Exception:
        pass
    return packages

def auto_install_packages(filepath, logpath):
    packages = extract_imports(filepath)
    if not packages:
        return [], []
    installed = []
    failed = []
    name_map = {'telebot': 'pyTelegramBotAPI', 'telegram': 'python-telegram-bot', 'PIL': 'Pillow', 'cv2': 'opencv-python', 'bs4': 'beautifulsoup4', 'yaml': 'PyYAML', 'dotenv': 'python-dotenv', 'requests': 'requests', 'aiohttp': 'aiohttp', 'flask': 'flask', 'fastapi': 'fastapi', 'uvicorn': 'uvicorn', 'numpy': 'numpy', 'pandas': 'pandas', 'discord': 'discord.py', 'yt_dlp': 'yt-dlp'}
    with open(logpath, 'a', encoding='utf-8') as log:
        log.write(f"\n--- [AUTO-PIP START {datetime.now()}] ---\n")
        for pkg in packages:
            pip_name = name_map.get(pkg, pkg)
            try:
                result = subprocess.run([sys.executable, "-m", "pip", "show", pip_name], capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    continue
                install = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--no-cache-dir", pip_name], capture_output=True, text=True, timeout=120)
                if install.returncode == 0:
                    installed.append(pip_name)
                else:
                    failed.append(pip_name)
            except Exception:
                failed.append(pip_name)
    return installed, failed

# ==================== CRASH GUARD ====================
def crash_guard_worker():
    while True:
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hosted_bots WHERE status = 'running'")
            running_bots = cursor.fetchall()
            for b in running_bots:
                pid = b['pid']
                if not is_process_alive(pid) if pid else True:
                    try:
                        proc = safe_popen(b['filepath'], b['logpath'])
                        cursor.execute("UPDATE hosted_bots SET pid = ? WHERE id = ?", (proc.pid, b['id']))
                        conn.commit()
                    except Exception:
                        pass
            conn.close()
        except Exception:
            pass
        time.sleep(8)

threading.Thread(target=crash_guard_worker, daemon=True).start()

# ==================== BUTTON PATCHING ====================
def _btn_to_dict_patch(original_to_dict):
    def patched(self):
        d = original_to_dict(self)
        style = getattr(self, "_style", None)
        icon = getattr(self, "_icon_custom_emoji_id", None)
        if style: d["style"] = style
        if icon: d["icon_custom_emoji_id"] = str(icon)
        return d
    return patched

if not getattr(types.InlineKeyboardButton, "_style_patched", False):
    types.InlineKeyboardButton.to_dict = _btn_to_dict_patch(types.InlineKeyboardButton.to_dict)
    types.InlineKeyboardButton._style_patched = True
if not getattr(types.KeyboardButton, "_style_patched", False):
    types.KeyboardButton.to_dict = _btn_to_dict_patch(types.KeyboardButton.to_dict)
    types.KeyboardButton._style_patched = True

def ibtn(text, callback_data=None, url=None, style=None, icon=None):
    kwargs = {}
    if callback_data: kwargs["callback_data"] = callback_data
    if url: kwargs["url"] = url
    btn = types.InlineKeyboardButton(text, **kwargs)
    if style: btn._style = style
    eid = EMOJI_IDS.get(icon) if icon else None
    if eid: btn._icon_custom_emoji_id = str(eid)
    return btn

def kbtn(text, style=None, icon=None):
    btn = types.KeyboardButton(text)
    if style: btn._style = style
    eid = EMOJI_IDS.get(icon) if icon else None
    if eid: btn._icon_custom_emoji_id = str(eid)
    return btn

# ==================== KEYBOARDS ====================
def main_reply_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True, row_width=2)
    markup.row(
        kbtn("Upload Bot", style="primary", icon="rocket"),
        kbtn("My Bots", style="primary", icon="bot"),
    )
    markup.row(kbtn("PRIME ZONE", style="danger", icon="diamond"))
    markup.row(
        kbtn("Admin Panel", style="primary", icon="settings"),
        kbtn("Status", style="primary", icon="refresh"),
    )
    markup.row(kbtn("Help", style="primary", icon="bell"))
    return markup

def now_ist_str():
    try:
        from datetime import timezone, timedelta
        ist = timezone(timedelta(hours=5, minutes=30))
        return datetime.now(ist).strftime("%d-%m-%Y %I:%M:%S %p IST")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " IST"

# ==================== ADMIN PANEL FUNCTIONS ====================
def admin_panel_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        ibtn("Bot Limits", callback_data="admin_change_limits", style="primary"),
        ibtn("Brand Name", callback_data="admin_set_brand", style="primary"),
    )
    markup.add(
        ibtn("Live Emojis", callback_data="admin_emojis", style="danger"),
        ibtn("Free Access", callback_data="admin_free_access", style="success"),
    )
    markup.add(
        ibtn("Channel Username", callback_data="admin_set_channel", style="primary"),
    )
    markup.add(
        ibtn("Admin Username", callback_data="admin_set_admin_user", style="danger"),
        ibtn("Bot Username", callback_data="admin_set_bot_user", style="danger"),
    )
    markup.add(
        ibtn("Pending Requests", callback_data="admin_pending", style="danger"),
        ibtn("Reload Config", callback_data="admin_reload", style="primary"),
    )
    markup.add(ibtn("Main Menu", callback_data="main_menu", style="primary"))
    return markup

def show_admin_panel(chat_id, msg_id=None):
    msg = (
        f'⚙️ <b>ADMIN PANEL</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'🏷 Brand: <b>{brand()}</b>\n'
        f'📦 Free Limit: <b>{config.get("free_limit", "Unlimited")}</b>\n'
        f'📢 Channel: @{config.get("channel_username") or "-"}\n'
        f'📞 Admin: @{config.get("admin_username") or "-"}\n'
        f'🤖 Bot: @{config.get("bot_username", "rkhosting3bot")}\n\n'
        f'Select option:'
    )
    send_or_edit(chat_id, msg, admin_panel_keyboard(), msg_id)

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    register_user(user_id)
    user_name = message.from_user.first_name or "User"

    welcome = (
        f'{pe("spark", "✨")} <b>{brand()}</b> {pe("spark", "✨")}\n'
        f'{pe("crown", "👑")} <b>{OWNER_NAME}</b> • v5.2\n'
        f'━━━━━━━━━━━━━━━━━━━━\n\n'
        f'{pe("wave", "👋")} Welcome, <b>{user_name}</b>!\n\n'
        f'{pe("card", "🪪")} <b>Profile</b>\n'
        f'├ {pe("user", "🏷")} Name: <code>{user_name}</code>\n'
        f'└ {pe("card", "🆔")} ID: <code>{user_id}</code>\n\n'
        f'{pe("top", "👇")} Use buttons below:'
    )
    bot.send_message(message.chat.id, welcome, parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    send_typing(message.chat.id)
    register_user(user_id)

    if not message.document.file_name or not message.document.file_name.lower().endswith('.py'):
        bot.reply_to(message, "❌ Only `.py` Python files are allowed.")
        return

    filename = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)

    user_dir = os.path.join(os.getcwd(), HOST_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, filename)
    logpath = filepath + ".log"

    with open(filepath, 'wb') as f:
        f.write(downloaded)

    with open(logpath, 'w', encoding='utf-8') as f:
        f.write(f"--- [UPLOADED {datetime.now()}] ---\n")

    now_str = now_ist_str()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO hosted_bots (user_id, filename, filepath, logpath, status, created_at) VALUES (?, ?, ?, ?, 'stopped', ?)",
        (user_id, filename, filepath, logpath, now_str)
    )
    conn.commit()
    conn.close()

    auto_install_packages(filepath, logpath)

    bot.reply_to(
        message,
        f'{pe("check", "✅")} <code>{html_mod.escape(filename)}</code> uploaded successfully and ready to start!\n'
        f'Go to <b>My Bots</b> to run it.',
        parse_mode="HTML",
    )

# ==================== BOTTOM MENU HANDLER ====================
@bot.message_handler(func=lambda m: m.text in {
    "Upload Bot", "My Bots", "PRIME ZONE", "Status", "Help", "Channel", "Support", "Admin Panel"
})
def bottom_menu_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    send_typing(chat_id)
    register_user(user_id)

    if text == "Upload Bot":
        bot.send_message(chat_id, f'{pe("rocket", "📥")} Send your <code>.py</code> file here.', parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))
    elif text == "My Bots":
        _show_my_bots(chat_id, user_id)
    elif text == "Admin Panel":
        show_admin_panel(chat_id)
    elif text == "PRIME ZONE":
        prime_text = (
            f'{pe("diamond", "💎")} <b>PRIME ZONE</b> {pe("diamond", "💎")}\n'
            f'━━━━━━━━━━━━━━━━━━━━\n\n'
            f'{pe("spark", "✨")} All hosting features are completely unlocked and free for everyone!\n'
            f'{pe("check", "✅")} Unlimited Bot Uploads\n'
            f'{pe("check", "✅")} 24/7 Uptime with Flask\n'
            f'{pe("check", "✅")} Auto Package Installer Active'
        )
        bot.send_message(chat_id, prime_text, parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))
    elif text == "Status":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM hosted_bots")
        total = cursor.fetchone()['total']
        cursor.execute("SELECT COUNT(*) as running FROM hosted_bots WHERE status='running'")
        running = cursor.fetchone()['running']
        conn.close()
        bot.send_message(chat_id, f'🖥️ *Server Status*\n🤖 Hosted Bots: `{total}`\n🟢 Running: `{running}`', parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))
    elif text == "Help":
        bot.send_message(chat_id, '❓ Upload any `.py` file, go to **My Bots**, and click **Start**!', parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))
    else:
        bot.send_message(chat_id, "Feature unavailable.", reply_markup=main_reply_keyboard(user_id))

def _show_my_bots(chat_id, user_id, msg_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hosted_bots WHERE user_id = ? ORDER BY id DESC", (user_id,))
    bots = cursor.fetchall()
    conn.close()
    if not bots:
        bot.send_message(chat_id, f'{pe("cross", "❌")} No bots found.', parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))
        return
    markup = types.InlineKeyboardMarkup()
    for b in bots:
        alive = b['status'] == 'running' and b['pid'] and is_process_alive(b['pid'])
        icon = "🟢" if alive else "🔴"
        label = f"{icon} {b['filename']}"
        markup.add(ibtn(label[:40], callback_data=f"manage_{b['id']}", style="primary", icon="bot"))
    markup.add(ibtn("Main Menu", callback_data="main_menu", style="danger", icon="top"))
    send_or_edit(chat_id, "⚙️ *Your Bots:*", markup, msg_id)

# ==================== CALLBACKS ====================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    user_id = call.from_user.id
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data

    if data == "main_menu":
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
        bot.send_message(chat_id, f'{pe("top", "🏠")} <b>Main Menu</b>', parse_mode="HTML", reply_markup=main_reply_keyboard(user_id))
    elif data == "my_bots":
        _show_my_bots(chat_id, user_id, msg_id)
    elif data == "admin_panel":
        show_admin_panel(chat_id, msg_id)
    elif data == "admin_change_limits":
        m = bot.send_message(chat_id, "✏️️ Enter new bot limits:\nFormat: <code>Free, Prime</code>\nExample: <code>3, 10</code>", parse_mode="HTML")
        bot.register_next_step_handler(m, process_admin_set_limits)
    elif data == "admin_set_brand":
        m = bot.send_message(chat_id, "✏️ Send new <b>Brand Name</b>:", parse_mode="HTML")
        bot.register_next_step_handler(m, process_admin_set_brand)
    elif data == "admin_emojis":
        try:
            bot.answer_callback_query(call.id, "Opening Emoji Manager...")
        except Exception:
            pass
    elif data == "admin_free_access":
        try:
            bot.answer_callback_query(call.id, "Free Access settings selected")
        except Exception:
            pass
    elif data == "admin_set_channel":
        m = bot.send_message(chat_id, "✏️ Enter Channel username (without @):\nSend <code>none</code> to disable.", parse_mode="HTML")
        bot.register_next_step_handler(m, process_admin_set_channel)
    elif data == "admin_set_admin_user":
        m = bot.send_message(chat_id, "✏️ Enter Admin username (without @):", parse_mode="HTML")
        bot.register_next_step_handler(m, process_admin_set_admin_user)
    elif data == "admin_set_bot_user":
        m = bot.send_message(chat_id, "✏️ Enter Bot username (without @):", parse_mode="HTML")
        bot.register_next_step_handler(m, process_admin_set_bot_user)
    elif data == "admin_pending":
        try:
            bot.answer_callback_query(call.id, "Fetching pending requests...")
        except Exception:
            pass
    elif data == "admin_reload":
        try:
            bot.answer_callback_query(call.id, "✅ Config reloaded successfully!", show_alert=True)
        except Exception:
            pass
        show_admin_panel(chat_id, msg_id)
    elif data.startswith("manage_"):
        bot_id = int(data.split("_")[1])
        render_bot_control(chat_id, bot_id, msg_id, user_id)
    elif data.startswith("startbot_"):
        bot_id = int(data.split("_")[1])
        start_bot_action(chat_id, bot_id, msg_id, user_id)
    elif data.startswith("stopbot_"):
        bot_id = int(data.split("_")[1])
        stop_bot_action(chat_id, bot_id, msg_id, user_id)
    elif data.startswith("logbot_"):
        bot_id = int(data.split("_")[1])
        show_logs_action(chat_id, bot_id, msg_id)
    elif data.startswith("clearlog_"):
        bot_id = int(data.split("_")[1])
        clear_logs_action(chat_id, bot_id, msg_id)
    elif data.startswith("delbot_"):
        bot_id = int(data.split("_")[1])
        delete_bot_action(chat_id, bot_id, msg_id, user_id)

def process_admin_set_brand(message):
    new_brand = message.text.strip()
    config["brand_name"] = new_brand
    bot.reply_to(message, f"✅ Brand name successfully updated to: <b>{new_brand}</b>", parse_mode="HTML")

def process_admin_set_channel(message):
    val = message.text.strip().lstrip("@")
    if val.lower() == "none":
        val = ""
    config["channel_username"] = val
    bot.reply_to(message, f"✅ Channel username updated: <code>{val or 'Disabled'}</code>", parse_mode="HTML")

def process_admin_set_limits(message):
    val = message.text.strip()
    config["free_limit"] = val
    bot.reply_to(message, f"✅ Bot limits updated: <code>{val}</code>", parse_mode="HTML")

def process_admin_set_admin_user(message):
    val = message.text.strip().lstrip("@")
    config["admin_username"] = val
    bot.reply_to(message, f"✅ Admin username updated: <code>{val}</code>", parse_mode="HTML")

def process_admin_set_bot_user(message):
    val = message.text.strip().lstrip("@")
    config["bot_username"] = val
    bot.reply_to(message, f"✅ Bot username updated: <code>{val}</code>", parse_mode="HTML")

def render_bot_control(chat_id, bot_id, msg_id=None, user_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hosted_bots WHERE id = ?", (bot_id,))
    b = cursor.fetchone()
    conn.close()

    if not b or (user_id and b['user_id'] != user_id):
        bot.send_message(chat_id, "❌ Bot not found.")
        return

    alive = b['status'] == 'running' and b['pid'] and is_process_alive(b['pid'])
    status = "🟢 Running" if alive else "🔴 Stopped"

    msg = f"🤖 *Bot Control*\n📄 File: `{b['filename']}`\n📊 Status: {status}"
    markup = types.InlineKeyboardMarkup(row_width=2)
    if alive:
        markup.add(ibtn("Stop", callback_data=f"stopbot_{b['id']}", style="danger", icon="cross"))
    else:
        markup.add(ibtn("Start", callback_data=f"startbot_{b['id']}", style="primary", icon="rocket"))
    markup.add(
        ibtn("Logs", callback_data=f"logbot_{b['id']}", style="primary", icon="bell"),
        ibtn("Clear Logs", callback_data=f"clearlog_{b['id']}", style="danger", icon="warning"),
    )
    markup.add(ibtn("Delete", callback_data=f"delbot_{b['id']}", style="danger", icon="cross"))
    markup.add(ibtn("My Bots", callback_data="my_bots", style="danger", icon="bot"))
    send_or_edit(chat_id, msg, markup, msg_id)

def start_bot_action(chat_id, bot_id, msg_id, user_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hosted_bots WHERE id = ?", (bot_id,))
    b = cursor.fetchone()
    if b and (not user_id or b['user_id'] == user_id):
        if not b['pid'] or not is_process_alive(b['pid']):
            try:
                process = safe_popen(b['filepath'], b['logpath'])
                cursor.execute("UPDATE hosted_bots SET status = 'running', pid = ? WHERE id = ?", (process.pid, bot_id))
                conn.commit()
            except Exception:
                pass
    conn.close()
    render_bot_control(chat_id, bot_id, msg_id, user_id)

def stop_bot_action(chat_id, bot_id, msg_id, user_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hosted_bots WHERE id = ?", (bot_id,))
    b = cursor.fetchone()
    if b and (not user_id or b['user_id'] == user_id):
        if b['pid']:
            safe_kill(b['pid'])
        cursor.execute("UPDATE hosted_bots SET status = 'stopped', pid = NULL WHERE id = ?", (bot_id,))
        conn.commit()
    conn.close()
    render_bot_control(chat_id, bot_id, msg_id, user_id)

def show_logs_action(chat_id, bot_id, msg_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hosted_bots WHERE id = ?", (bot_id,))
    b = cursor.fetchone()
    conn.close()
    if not b or not os.path.exists(b['logpath']):
        bot.send_message(chat_id, "❌ Log file not found.")
        return
    with open(b['logpath'], 'r', encoding='utf-8', errors='ignore') as f:
        last = "".join(f.readlines()[-40:]).strip() or "No logs yet."
    msg = f"📜 *Logs* — `{b['filename']}`\n```\n{last[-3500:]}\n```"
    markup = types.InlineKeyboardMarkup()
    markup.add(ibtn("Refresh", callback_data=f"logbot_{bot_id}", style="primary", icon="refresh"))
    markup.add(ibtn("Back", callback_data=f"manage_{bot_id}", style="danger", icon="top"))
    send_or_edit(chat_id, msg, markup, msg_id)

def clear_logs_action(chat_id, bot_id, msg_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT logpath FROM hosted_bots WHERE id = ?", (bot_id,))
    b = cursor.fetchone()
    conn.close()
    if b and os.path.exists(b['logpath']):
        with open(b['logpath'], 'w', encoding='utf-8') as f:
            f.write(f"--- [CLEARED {datetime.now()}] ---\n")
    show_logs_action(chat_id, bot_id, msg_id)

def delete_bot_action(chat_id, bot_id, msg_id, user_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hosted_bots WHERE id = ?", (bot_id,))
    b = cursor.fetchone()
    if b and (not user_id or b['user_id'] == user_id):
        if b['pid']: safe_kill(b['pid'])
        for path in [b['filepath'], b['logpath']]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except Exception: pass
        cursor.execute("DELETE FROM hosted_bots WHERE id = ?", (bot_id,))
        conn.commit()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 My Bots", callback_data="my_bots"))
    send_or_edit(chat_id, "🗑️ Bot deleted.", markup, msg_id)

# ==================== START ====================
if __name__ == '__main__':
    keep_alive()  # Start Flask server for 24/7 uptime
    print(f"👑 {OWNER_NAME}")
    print(f"⚡ Free Hosting v5.2 with Flask and Admin Panel running!")
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
