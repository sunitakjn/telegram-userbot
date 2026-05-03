import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
# Bot Token aur Owner ID
BOT_TOKEN = '8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA'
OWNER_ID = 8442352135 

# API Configuration (Nayi API ke hisab se)
API_URL = "https://cortex-hosting.gt.tc/"
API_KEY = "j4tnx"

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

def get_chat_display(chat_id):
    try:
        chat = bot.get_chat(chat_id)
        if chat.title: return f"**{chat.title}** (`{chat_id}`)"
        return f"`{chat_id}`"
    except: return f"`{chat_id}`"

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=[
    'approvegc', 'disapprovegc', 'disapprovegcall', 'listapprovegc', 
    'approvebot', 'disapprovebot', 'disapprovebotall', 'listapprovebot', 
    'unprotect', 'protect', 'unprotectall', 'listprotect', 
    'unlimited', 'disunlimited', 'disunlimitedall', 'listunlimited', 'tg', 'broadcast'
])
def handle_commands(message):
    cmd = message.text.split()[0].split('@')[0].lower()
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # --- OWNER ONLY COMMANDS ---
    if user_id == OWNER_ID:
        if cmd == '/broadcast':
            groups = load_list(DB_FILE)
            if not groups:
                bot.reply_to(message, "❌ No approved groups found.")
                return
            
            success, failed = 0, 0
            for gid in groups:
                try:
                    if message.reply_to_message:
                        bot.copy_message(gid, message.chat.id, message.reply_to_message.message_id)
                    else:
                        text = message.text[len('/broadcast '):].strip()
                        if not text: return
                        bot.send_message(gid, text)
                    success += 1
                except: failed += 1
            bot.reply_to(message, f"📢 **Broadcast Complete**\n✅ Success: `{success}`\n❌ Failed: `{failed}`", parse_mode="Markdown")

        elif cmd == '/approvebot':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (message.text.split()[1] if len(message.text.split()) > 1 else None)
            if tid and add_to_list(USER_APPROVAL_FILE, tid):
                bot.reply_to(message, f"✅ User `{tid}` approved for personal access.")

        elif cmd == '/approvegc':
            if add_to_list(DB_FILE, message.chat.id): bot.reply_to(message, "✅ Group Approved!")

        # ... (Baaki saare delete/list commands aapke original code se active rahenge) ...

    # --- MAIN SEARCH COMMAND (/tg) ---
    if cmd == '/tg':
        if not is_subscribed(user_id):
            bot.reply_to(message, "⚠️ Join all channels to use this bot:", reply_markup=get_join_markup())
            return

        # Check Access
        is_group_approved = str(message.chat.id) in load_list(DB_FILE)
        is_user_approved = user_id_str in load_list(USER_APPROVAL_FILE)
        
        if not (is_group_approved or is_user_approved or user_id == OWNER_ID):
            bot.reply_to(message, "🚫 Access Denied. Group not approved or no personal access.")
            return
        
        # Limit Check
        usage = load_usage()
        is_special = (user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE))
        
        if not is_special:
            if usage.get(user_id_str, 0) >= 15:
                bot.reply_to(message, "❌ Daily limit (15) reached.")
                return
            usage[user_id_str] = usage.get(user_id_str, 0) + 1
            save_usage(usage)
            left_text = f"{15 - usage[user_id_str]}/15"
        else:
            left_text = "Unlimited"

        # Get Search Term
        args = message.text.split()
        term = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args) > 1 else None)
        
        if not term:
            bot.reply_to(message, "Usage: `/tg <number/id>`", parse_mode="Markdown")
            return
        
        if term in load_list(PROTECTED_DATA_FILE):
            bot.reply_to(message, f"🎯 **TARGET:** `{term}`\n🛡️ **RESULT:** `Protected User`", parse_mode="Markdown")
            return

        # Developer Button
        dev_markup = InlineKeyboardMarkup()
        dev_markup.add(InlineKeyboardButton(text="𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/sxdad"))

        wait_msg = bot.reply_to(message, "🔍 Searching in Database...")
        
        try:
            # New API Integration
            api_res = requests.get(API_URL, params={'key': API_KEY, 'term': term}, timeout=10).json()
            
            if api_res.get("status") is True:
                data = api_res.get("data", {})
                p_info = data.get("phone_info", {})
                
                ui = (
                    f"🎯 **TARGET:** `{term}`\n"
                    f"👤 **Name:** `{data.get('display_name', 'N/A')}`\n"
                    f"🆔 **Username:** @{data.get('username', 'N/A')}\n"
                    f"🔢 **User ID:** `{data.get('user_id', 'N/A')}`\n"
                    f"🌍 **Country:** `{p_info.get('country', 'N/A')}`\n"
                    f"📞 **Phone:** `{p_info.get('country_code', '')} {p_info.get('number', 'N/A')}`\n"
                    f"📊 **Searches Left:** `{left_text}`\n\n"
                    f"🗑️ *Auto-delete in 30 seconds*"
                )
                final_msg = bot.edit_message_text(ui, message.chat.id, wait_msg.message_id, parse_mode="Markdown", reply_markup=dev_markup)
                threading.Thread(target=delete_later, args=(message.chat.id, final_msg.message_id, 30)).start()
            else:
                bot.edit_message_text("❌ No data found for this target.", message.chat.id, wait_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"⚠️ API Error: Connection failed.", message.chat.id, wait_msg.message_id)

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

if __name__ == "__main__":
    print("Bot is live...")
    bot.infinity_polling()
            
