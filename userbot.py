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
        return f"**{chat.title or chat.username}** (`{chat_id}`)"
    except: return f"`{chat_id}`"

def get_target_id(message):
    args = message.text.split()
    if message.reply_to_message:
        return str(message.reply_to_message.from_user.id)
    return args[1] if len(args) > 1 else None

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=[
    'approvegc', 'disapprovegc', 'disapprovegcall', 'listapprovegc', 
    'approvebot', 'disapprovebot', 'disapprovebotall', 'listapprovebot', 
    'unprotect', 'protect', 'unprotectall', 'listprotect', 
    'unlimited', 'disunlimited', 'disunlimitedall', 'listunlimited', 'broadcast'
])
def admin_commands(message):
    cmd = message.text.split()[0].split('@')[0].lower()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return bot.reply_to(message, "❌ Only Owner can use this.")

    if cmd == '/broadcast':
        groups = load_list(DB_FILE)
        if not groups: return bot.reply_to(message, "❌ No groups.")
        success, failed = 0, 0
        for gid in groups:
            try:
                if message.reply_to_message:
                    bot.copy_message(gid, message.chat.id, message.reply_to_message.message_id)
                else:
                    txt = message.text[len('/broadcast '):].strip()
                    if txt: bot.send_message(gid, txt)
                success += 1
            except: failed += 1
        bot.reply_to(message, f"📢 Broadcast: ✅ {success} | ❌ {failed}")

    elif cmd == '/approvegc':
        if add_to_list(DB_FILE, message.chat.id): bot.reply_to(message, "✅ Group Approved!")
    
    elif cmd == '/disapprovegc':
        if remove_from_list(DB_FILE, message.chat.id): bot.reply_to(message, "🚫 Group Disapproved!")

    elif cmd == '/listapprovegc':
        groups = load_list(DB_FILE)
        msg = "🏢 **Groups:**\n" + "\n".join([f"{i+1}. {get_chat_display(g)}" for i, g in enumerate(groups)])
        bot.reply_to(message, msg or "Empty", parse_mode="Markdown")

    # Add other admin logic (protect/unlimited) here if needed...

@bot.message_handler(commands=['tg'])
def search_tg(message):
    user_id = message.from_user.id
    user_id_str = str(user_id)
    
    # 1. Check Subscription
    if not is_subscribed(user_id):
        bot.reply_to(message, "⚠️ Join channels first:", reply_markup=get_join_markup())
        return

    # 2. Check Access (Group or User)
    is_group_ok = str(message.chat.id) in load_list(DB_FILE)
    is_user_ok = user_id_str in load_list(USER_APPROVAL_FILE)
    if not (is_group_ok or is_user_ok or user_id == OWNER_ID):
        bot.reply_to(message, "🚫 Access Denied.")
        return

    # 3. Handle Limits
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

    # 4. Target Logic
    term = get_target_id(message)
    if not term:
        bot.reply_to(message, "Usage: `/tg <id>`")
        return

    if term in load_list(PROTECTED_DATA_FILE):
        bot.reply_to(message, f"🛡️ Target `{term}` is Protected.")
        return

    wait_msg = bot.reply_to(message, "🔍 Searching...")
    
    try:
        response = requests.get(f"{API_BASE_URL}{term}", timeout=15)
        res = response.json()
        
        if res.get('status') == True and 'data' in res:
            data = res['data']
            p_info = data.get('phone_info', {})
            
            ui = (
                f"👤 **Name:** `{data.get('display_name', 'N/A')}`\n"
                f"🔗 **Username:** `@{data.get('username', 'N/A')}`\n"
                f"🆔 **TG ID:** `{p_info.get('tg_id', 'N/A')}`\n"
                f"📱 **Number:** `{p_info.get('country_code', '')}{p_info.get('number', 'N/A')}`\n"
                f"🌍 **Country:** `{p_info.get('country', 'N/A')}`\n\n"
                f"📊 **Searches Left:** `{left_text}`\n"
                f"🗑️ *Deleting in 30s*"
            )
            dev_markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text="𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/sxdad"))
            final_msg = bot.edit_message_text(ui, message.chat.id, wait_msg.message_id, parse_mode="Markdown", reply_markup=dev_markup)
            threading.Thread(target=delete_later, args=(message.chat.id, final_msg.message_id, 30)).start()
        else:
            bot.edit_message_text("⚠️ No data found.", message.chat.id, wait_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ API Error.", message.chat.id, wait_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
    
