import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAFb5oMGFVREoVR5H58TpAbpTho7DEWSOcc'
# Base URL ko clean rakha hai params ke liye
API_URL = "https://cortex-hosting.gt.tc/" 
API_KEY = "j4tnx"
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

def clear_file(file):
    with open(file, "w") as f:
        f.truncate(0)

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
        if chat.username: return f"@{chat.username} (`{chat_id}`)"
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

    # OWNER ONLY COMMANDS
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

        elif cmd == '/disunlimitedall':
            clear_file(UNLIMITED_FILE)
            bot.reply_to(message, "🗑️ Unlimited list cleared.")

        elif cmd == '/unprotectall':
            clear_file(PROTECTED_DATA_FILE)
            bot.reply_to(message, "🗑️ Protection list cleared.")

        elif cmd == '/disapprovegcall':
            clear_file(DB_FILE)
            bot.reply_to(message, "🗑️ All Groups removed.")

        elif cmd == '/disapprovebotall':
            clear_file(USER_APPROVAL_FILE)
            bot.reply_to(message, "🗑️ All users removed from personal access.")

        elif cmd == '/approvebot':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (message.text.split()[1] if len(message.text.split()) > 1 else None)
            if tid and add_to_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"✅ `{tid}` Approved.")
        
        elif cmd == '/disapprovebot':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (message.text.split()[1] if len(message.text.split()) > 1 else None)
            if tid and remove_from_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"🚫 `{tid}` Removed.")

        elif cmd == '/approvegc':
            if add_to_list(DB_FILE, message.chat.id): bot.reply_to(message, "✅ Group Approved!")
        
        elif cmd == '/disapprovegc':
            if remove_from_list(DB_FILE, message.chat.id): bot.reply_to(message, "🚫 Group Disapproved!")

        # ... other list/management commands can be added here similarly ...

    # SEARCH COMMAND
    if cmd == '/tg':
        if not is_subscribed(user_id):
            bot.reply_to(message, "⚠️ Join all channels to use this bot:", reply_markup=get_join_markup())
            return

        chat_id_str = str(message.chat.id)
        is_group_approved = chat_id_str in load_list(DB_FILE)
        is_user_approved = user_id_str in load_list(USER_APPROVAL_FILE)
        
        if not (is_group_approved or is_user_approved or user_id == OWNER_ID):
            bot.reply_to(message, "🚫 Access Denied.")
            return
        
        usage = load_usage()
        is_special = (user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE))
        
        if not is_special:
            if usage.get(user_id_str, 0) >= 15:
                bot.reply_to(message, "❌ Daily limit reached.")
                return
            usage[user_id_str] = usage.get(user_id_str, 0) + 1
            save_usage(usage)
            left_text = f"{15 - usage[user_id_str]}/15"
        else:
            left_text = "Unlimited"

        args = message.text.split()
        term = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args) > 1 else None)
        
        if not term:
            bot.reply_to(message, "Usage: `/tg <id>`")
            return
        
        if term in load_list(PROTECTED_DATA_FILE):
            bot.reply_to(message, f"🎯 **TARGET:** `{term}`\n❌ **RESULT:** `Protected`")
            return

        dev_markup = InlineKeyboardMarkup()
        dev_markup.add(InlineKeyboardButton(text="𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/sxdad"))

        wait_msg = bot.reply_to(message, "🔍 Searching...")
        try:
            # --- FIXED API PARSING LOGIC ---
            response = requests.get(API_URL, params={'key': API_KEY, 'term': term}, timeout=10).json()
            
            data = response.get("data", {})
            phone_info = data.get("phone_info", {})
            
            num = phone_info.get("number", "N/A")
            country = phone_info.get("country", "N/A")
            c_code = phone_info.get("country_code", "")

            full_num = f"{c_code}{num}" if num != "N/A" else "N/A"

            ui = (
                f"🎯 **TARGET:** `{term}`\n"
                f"📱 **Number:** `{full_num}`\n"
                f"🌍 **Country:** `{country}`\n"
                f"📊 **Searches Left:** `{left_text}`\n\n"
                f"🗑️ *This Message Will Delete In 30 Seconds*"
            )
            final_msg = bot.edit_message_text(ui, message.chat.id, wait_msg.message_id, parse_mode="Markdown", reply_markup=dev_markup)
            threading.Thread(target=delete_later, args=(message.chat.id, final_msg.message_id, 30)).start()
        except:
            bot.edit_message_text("⚠️ Data Not Found.", message.chat.id, wait_msg.message_id)

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
        
