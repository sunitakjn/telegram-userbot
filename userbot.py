import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAFb5oMGFVREoVR5H58TpAbpTho7DEWSOcc'
API_BASE_URL = "https://cortex-hosting.gt.tc/?key=j4tnx&term="
OWNER_ID = 8442352135 

# --- FORCE JOIN CONFIG ---
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
        for item in items_list:
            f.write(f"{item}\n")

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

def get_target_id(message):
    args = message.text.split()
    if message.reply_to_message:
        return str(message.reply_to_message.from_user.id)
    return args[1] if len(args) > 1 else None

def delete_later(chat_id, message_id, delay):
    time.sleep(delay)
    try: bot.delete_message(chat_id, message_id)
    except: pass

# --- COMMAND HANDLERS ---

@bot.message_handler(commands=['tg'])
def search_handler(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)

    if not is_subscribed(user_id):
        bot.reply_to(message, "⚠️ Join channels first:", reply_markup=get_join_markup())
        return

    is_group_ok = str(message.chat.id) in load_list(DB_FILE)
    is_user_ok = user_id_str in load_list(USER_APPROVAL_FILE)
    
    if not (is_group_ok or is_user_ok or user_id == OWNER_ID):
        bot.reply_to(message, "🚫 Access Denied (Group/User not approved).")
        return

    # Usage Limits
    usage = load_usage()
    is_special = (user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE))
    
    if not is_special:
        count = usage.get(user_id_str, 0)
        if count >= 15:
            bot.reply_to(message, "❌ Daily limit (15) reached.")
            return
        usage[user_id_str] = count + 1
        save_usage(usage)
        left_text = f"{15 - usage[user_id_str]}/15"
    else:
        left_text = "Unlimited"

    term = get_target_id(message)
    if not term:
        bot.reply_to(message, "Usage: `/tg <id>` or reply to someone.")
        return

    if term in load_list(PROTECTED_DATA_FILE):
        bot.reply_to(message, "🛡️ Result: `Protected by Admin`")
        return

    wait = bot.reply_to(message, "🔍 Searching Data...")

    try:
        res = requests.get(f"{API_BASE_URL}{term}", timeout=15).json()
        if res.get('status'):
            data = res['data']
            p = data.get('phone_info', {})
            ui = (
                f"👤 **Name:** `{data.get('display_name', 'N/A')}`\n"
                f"🔗 **Username:** `@{data.get('username', 'N/A')}`\n"
                f"🆔 **TG ID:** `{p.get('tg_id', 'N/A')}`\n"
                f"📱 **Number:** `{p.get('country_code', '')}{p.get('number', 'N/A')}`\n"
                f"🌍 **Country:** `{p.get('country', 'N/A')}`\n\n"
                f"📊 **Searches Left:** `{left_text}`\n"
                f"🗑️ *Deleting in 30s*"
            )
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/sxdad"))
            msg = bot.edit_message_text(ui, message.chat.id, wait.message_id, parse_mode="Markdown", reply_markup=markup)
            threading.Thread(target=delete_later, args=(message.chat.id, msg.message_id, 30)).start()
        else:
            bot.edit_message_text("⚠️ No data found.", message.chat.id, wait.message_id)
    except:
        bot.edit_message_text("⚠️ API Error.", message.chat.id, wait.message_id)

@bot.message_handler(func=lambda m: m.from_user.id == OWNER_ID, commands=[
    'approvegc', 'disapprovegc', 'listapprovegc', 'protect', 'unprotect', 
    'unlimited', 'disunlimited', 'approvebot', 'disapprovebot'
])
def admin_tools(message):
    cmd = message.text.split()[0].lower()
    tid = get_target_id(message)

    if 'approvegc' in cmd:
        if add_to_list(DB_FILE, message.chat.id): bot.reply_to(message, "✅ GC Approved.")
    elif 'protect' in cmd and tid:
        if add_to_list(PROTECTED_DATA_FILE, tid): bot.reply_to(message, f"🛡️ `{tid}` Protected.")
    elif 'unlimited' in cmd and tid:
        if add_to_list(UNLIMITED_FILE, tid): bot.reply_to(message, f"🚀 `{tid}` is Unlimited.")
    elif 'approvebot' in cmd and tid:
        if add_to_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"👤 `{tid}` Personal Access ON.")
    # You can add more admin logic here as per the same pattern

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

# --- FIXED POLLING FOR RAILWAY ---
if __name__ == "__main__":
    print("Bot is Alive...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
            
