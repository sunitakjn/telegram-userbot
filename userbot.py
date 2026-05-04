import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAFb5oMGFVREoVR5H58TpAbpTho7DEWSOcc'
API_URL = "https://tg-num-api.onrender.com/tg" # Aapki Render API
OWNER_ID = 8442352135 

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

# --- HELPERS ---
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
        with open(file, "r") as f: return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_list(file, items_list):
    with open(file, "w") as f:
        for item in items_list: f.write(f"{item}\n")

def add_to_list(file, item):
    items = load_list(file)
    if str(item) not in items:
        items.append(str(item)); save_list(file, items); return True
    return False

def remove_from_list(file, item):
    items = load_list(file); item_str = str(item)
    if item_str in items:
        items.remove(item_str); save_list(file, items); return True
    return False

def load_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_usage(data):
    with open(USAGE_FILE, "w") as f: json.dump(data, f)

# --- AUTO DELETE FUNCTION ---
def auto_delete(chat_id, msg_ids, delay):
    time.sleep(delay)
    for msg_id in msg_ids:
        try: bot.delete_message(chat_id, msg_id)
        except: pass

# --- COMMANDS ---
@bot.message_handler(commands=['tg'])
def tg_search(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    chat_id = message.chat.id

    # 1. Force Join
    if not is_subscribed(user_id):
        bot.reply_to(message, "⚠️ Join all channels first:", reply_markup=get_join_markup())
        return

    # 2. Access Control
    is_group_ok = str(chat_id) in load_list(DB_FILE)
    is_user_ok = user_id_str in load_list(USER_APPROVAL_FILE)
    if not (is_group_ok or is_user_ok or user_id == OWNER_ID):
        bot.reply_to(message, "❌ Access Denied. Group not approved.")
        return

    # 3. Usage Limit
    usage = load_usage()
    is_special = (user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE))
    if not is_special:
        if usage.get(user_id_str, 0) >= 15:
            bot.reply_to(message, "❌ Daily limit (15) reached.")
            return
        usage[user_id_str] = usage.get(user_id_str, 0) + 1
        save_usage(usage)
        left = f"{15 - usage[user_id_str]}/15"
    else:
        left = "Unlimited"

    # 4. Target Detection
    args = message.text.split()
    term = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args) > 1 else None)
    
    if not term:
        bot.reply_to(message, "Usage: `/tg <id>` or reply to user.")
        return
    
    if term in load_list(PROTECTED_DATA_FILE) and user_id != OWNER_ID:
        bot.reply_to(message, "🛡️ ID Protected.")
        return

    # 5. Search Process
    wait_msg = bot.reply_to(message, "🔍 Searching API...")
    
    try:
        # API request
        res = requests.get(f"{API_URL}?id={term}", timeout=10).json()
        
        if res.get("success"):
            ui = (
                f"✨ **Search Results Found** ✨\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 **User ID:** `{res.get('user_id')}`\n"
                f"📞 **Number:** `{res.get('number')}`\n"
                f"🌍 **Country:** {res.get('Country')} ({res.get('Country Code')})\n"
                f"📊 **Searches Left:** `{left}`\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🗑️ *Deleting in 30 seconds...*"
            )
        else:
            ui = f"❌ No Data Found for `{term}`."

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/snxdad"))
        
        final_msg = bot.edit_message_text(ui, chat_id, wait_msg.message_id, parse_mode="Markdown", reply_markup=markup)

        # 6. Auto Delete (Threaded)
        threading.Thread(target=auto_delete, args=(chat_id, [message.message_id, final_msg.message_id], 30)).start()

    except Exception as e:
        bot.edit_message_text(f"⚠️ Error: API Connection failed.", chat_id, wait_msg.message_id)

# --- CALLBACKS & OWNER COMMANDS ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all first!", show_alert=True)

# Note: Include your other admin commands (/approvegc, etc.) here same as your provided code logic.

if __name__ == "__main__":
    bot.infinity_polling()
    
