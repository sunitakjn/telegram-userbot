import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA'
OWNER_ID = 8442352135 
API_URL = "https://cortex-hosting.gt.tc/"
API_KEY = "j4tnx"

# --- FORCE JOIN CHANNELS ---
CHANNELS = {
    "1 🚀": {"id": "@snxhub", "url": "https://t.me/snxhub"},
    "2 🚀": {"id": "@snnetwork7", "url": "https://t.me/snnetwork7"},
    "3 🚀": {"id": "@snxhub1", "url": "https://t.me/snxhub1"}
}

bot = telebot.TeleBot(BOT_TOKEN)

# --- DATABASE FILES ---
DB_FILE = "groups.txt"
USER_APPROVAL_FILE = "approved_users.txt"
UNLIMITED_FILE = "unlimited_users.txt"
PROTECTED_DATA_FILE = "protected_ids.txt"
USAGE_FILE = "usage_data.json"

# --- HELPER FUNCTIONS ---
def is_subscribed(user_id):
    if user_id == OWNER_ID: return True
    for name, data in CHANNELS.items():
        try:
            member = bot.get_chat_member(data["id"], user_id)
            if member.status in ['left', 'kicked', 'restricted']: return False
        except: return False
    return True

def get_join_markup():
    markup = InlineKeyboardMarkup()
    for name, data in CHANNELS.items():
        markup.add(InlineKeyboardButton(text=f"Join {name}", url=data["url"]))
    markup.add(InlineKeyboardButton(text="Verify ✅", callback_data="verify_user"))
    return markup

def load_list(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_list(file, items_list):
    with open(file, "w") as f:
        for item in items_list: f.write(f"{item}\n")

def clear_file(file):
    with open(file, "w") as f: f.truncate(0)

def add_to_list(file, item):
    items = load_list(file)
    if str(item) not in items:
        items.append(str(item))
        save_list(file, items)
        return True
    return False

def remove_from_list(file, item):
    items = load_list(file)
    if str(item) in items:
        items.remove(str(item))
        save_list(file, items)
        return True
    return False

def load_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_usage(data):
    with open(USAGE_FILE, "w") as f: json.dump(data, f)

def delete_later(chat_id, message_id, delay):
    time.sleep(delay)
    try: bot.delete_message(chat_id, message_id)
    except: pass

# --- CORE API FUNCTION (With Browser Headers) ---
def fetch_data(term):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    try:
        response = requests.get(API_URL, params={'key': API_KEY, 'term': term}, headers=headers, timeout=12)
        return response.json()
    except:
        return None

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=[
    'approvegc', 'disapprovegc', 'disapprovegcall', 'listapprovegc', 
    'approvebot', 'disapprovebot', 'disapprovebotall', 'listapprovebot', 
    'unprotect', 'protect', 'unprotectall', 'listprotect', 
    'unlimited', 'disunlimited', 'disunlimitedall', 'listunlimited', 'tg', 'broadcast', 'start'
])
def handle_commands(message):
    cmd = message.text.split()[0].split('@')[0].lower()
    user_id = message.from_user.id
    user_id_str = str(user_id)

    if cmd == '/start':
        bot.reply_to(message, "👋 Welcome! Use `/tg <id/number>` to search details.")
        return

    # OWNER ONLY LOGIC
    if user_id == OWNER_ID:
        if cmd == '/broadcast':
            groups = load_list(DB_FILE)
            if not groups: return bot.reply_to(message, "❌ No approved groups.")
            for gid in groups:
                try:
                    if message.reply_to_message: bot.copy_message(gid, message.chat.id, message.reply_to_message.message_id)
                    else: bot.send_message(gid, message.text[11:])
                except: pass
            bot.reply_to(message, "📢 Broadcast Sent!")
        
        elif cmd == '/approvegc':
            if add_to_list(DB_FILE, message.chat.id): bot.reply_to(message, "✅ Group Authorized.")
        elif cmd == '/approvebot':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (message.text.split()[1] if len(message.text.split()) > 1 else None)
            if tid and add_to_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"✅ User {tid} Approved.")
        # ... (Baaki Admin commands same load/save logic use karte hain)

    # SEARCH LOGIC (/tg)
    if cmd == '/tg':
        if not is_subscribed(user_id):
            return bot.reply_to(message, "⚠️ Subscribe to our channels first:", reply_markup=get_join_markup())

        if not (str(message.chat.id) in load_list(DB_FILE) or user_id_str in load_list(USER_APPROVAL_FILE) or user_id == OWNER_ID):
            return bot.reply_to(message, "🚫 Group or User not authorized.")

        usage = load_usage()
        if not (user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE)):
            if usage.get(user_id_str, 0) >= 15: return bot.reply_to(message, "❌ Limit Reached (15/15).")
            usage[user_id_str] = usage.get(user_id_str, 0) + 1
            save_usage(usage)

        args = message.text.split()
        term = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args) > 1 else None)
        
        if not term: return bot.reply_to(message, "Usage: `/tg <number>`")
        if term in load_list(PROTECTED_DATA_FILE): return bot.reply_to(message, "🛡️ Target is Protected.")

        wait_msg = bot.reply_to(message, "🔍 Connecting to API...")
        res = fetch_data(term)

        if res and res.get("status") is True:
            d = res.get("data", {})
            p = d.get("phone_info", {})
            
            # Developer Button logic
            dev_btn = InlineKeyboardMarkup().add(InlineKeyboardButton("𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/sxdad"))
            
            ui = (
                f"🎯 **TARGET:** `{term}`\n"
                f"👤 **Name:** `{d.get('display_name')}`\n"
                f"🆔 **User:** @{d.get('username')}\n"
                f"🔢 **ID:** `{d.get('user_id')}`\n"
                f"🌍 **Country:** `{p.get('country')}`\n"
                f"📞 **Phone:** `{p.get('country_code')} {p.get('number')}`\n\n"
                f"🗑️ *Auto-delete: 30s*"
            )
            final = bot.edit_message_text(ui, message.chat.id, wait_msg.message_id, parse_mode="Markdown", reply_markup=dev_btn)
            threading.Thread(target=delete_later, args=(message.chat.id, final.message_id, 30)).start()
        else:
            bot.edit_message_text("⚠️ Data not found or API error.", message.chat.id, wait_msg.message_id)

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Not Joined!", show_alert=True)

if __name__ == "__main__":
    bot.infinity_polling()
                            
