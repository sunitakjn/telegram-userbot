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
        return f"{chat.title or chat.username or 'Chat'} (`{chat_id}`)"
    except: return f"`{chat_id}`"

def get_target_id(message):
    args = message.text.split()
    if message.reply_to_message:
        return str(message.reply_to_message.from_user.id)
    return args[1] if len(args) > 1 else None

# --- COMMAND HANDLER ---
@bot.message_handler(commands=[
    'approvegc', 'disapprovegc', 'disapprovegcall', 'listapprovegc', 
    'approvebot', 'disapprovebot', 'disapprovebotall', 'listapprovebot', 
    'unprotect', 'protect', 'unprotectall', 'listprotect', 
    'unlimited', 'disunlimited', 'disunlimitedall', 'listunlimited', 'tg', 'broadcast'
])
def handle_commands(message):
    cmd = message.text.split()[0].split('@')[0].lower()
    user_id = message.from_user.id
    
    if user_id != OWNER_ID and cmd != '/tg':
        return bot.reply_to(message, "❌ Only Owner can use this command.")

    if cmd == '/approvegc':
        if add_to_list(DB_FILE, message.chat.id):
            bot.reply_to(message, f"✅ Group `{message.chat.id}` Approved!")
        else: bot.reply_to(message, "⚠️ Already approved.")

    elif cmd == '/disapprovegc':
        if remove_from_list(DB_FILE, message.chat.id):
            bot.reply_to(message, f"🚫 Group `{message.chat.id}` Disapproved!")
        else: bot.reply_to(message, "⚠️ Group not found in list.")

    elif cmd == '/disapprovegcall':
        clear_file(DB_FILE)
        bot.reply_to(message, "🗑️ All Approved Groups Cleared.")

    elif cmd == '/listapprovegc':
        groups = load_list(DB_FILE)
        msg = "🏢 **Approved Groups:**\n" + "\n".join([f"{i+1}. {get_chat_display(g)}" for i, g in enumerate(groups)]) if groups else "No groups."
        bot.reply_to(message, msg, parse_mode="Markdown")

    elif cmd == '/protect':
        tid = get_target_id(message)
        if tid and add_to_list(PROTECTED_DATA_FILE, tid):
            bot.reply_to(message, f"🛡️ ID `{tid}` is now Protected.")
        else: bot.reply_to(message, "❌ Use: `/protect <id>` or reply.")

    elif cmd == '/unprotect':
        tid = get_target_id(message)
        if tid and remove_from_list(PROTECTED_DATA_FILE, tid):
            bot.reply_to(message, f"🔓 ID `{tid}` is Unprotected.")
        else: bot.reply_to(message, "⚠️ ID not protected.")

    elif cmd == '/unprotectall':
        clear_file(PROTECTED_DATA_FILE)
        bot.reply_to(message, "🗑️ Protected IDs list cleared.")

    elif cmd == '/listprotect':
        pro = load_list(PROTECTED_DATA_FILE)
        msg = "🛡️ **Protected IDs:**\n" + "\n".join([f"{i+1}. `{u}`" for i, u in enumerate(pro)]) if pro else "Empty."
        bot.reply_to(message, msg, parse_mode="Markdown")

    elif cmd == '/unlimited':
        tid = get_target_id(message)
        if tid and add_to_list(UNLIMITED_FILE, tid):
            bot.reply_to(message, f"🚀 `{tid}` added to Unlimited.")
        else: bot.reply_to(message, "❌ Use: `/unlimited <id>` or reply.")

    elif cmd == '/disunlimited':
        tid = get_target_id(message)
        if tid and remove_from_list(UNLIMITED_FILE, tid):
            bot.reply_to(message, f"❌ `{tid}` removed from Unlimited.")
        else: bot.reply_to(message, "⚠️ User not in list.")

    elif cmd == '/disunlimitedall':
        clear_file(UNLIMITED_FILE)
        bot.reply_to(message, "🗑️ Unlimited list cleared.")

    elif cmd == '/listunlimited':
        unl = load_list(UNLIMITED_FILE)
        msg = "🚀 **Unlimited Users:**\n" + "\n".join([f"{i+1}. `{u}`" for i, u in enumerate(unl)]) if unl else "Empty."
        bot.reply_to(message, msg, parse_mode="Markdown")

    elif cmd == '/approvebot':
        tid = get_target_id(message)
        if tid and add_to_list(USER_APPROVAL_FILE, tid):
            bot.reply_to(message, f"👤 User `{tid}` Personal Access Approved.")
        else: bot.reply_to(message, "❌ Use: `/approvebot <id>` or reply.")

    elif cmd == '/disapprovebot':
        tid = get_target_id(message)
        if tid and remove_from_list(USER_APPROVAL_FILE, tid):
            bot.reply_to(message, f"🚫 User `{tid}` Personal Access Removed.")
        else: bot.reply_to(message, "⚠️ User not in list.")

    elif cmd == '/disapprovebotall':
        clear_file(USER_APPROVAL_FILE)
        bot.reply_to(message, "🗑️ All Personal Access Cleared.")

    elif cmd == '/listapprovebot':
        users = load_list(USER_APPROVAL_FILE)
        msg = "👤 **Personal Approved Users:**\n" + "\n".join([f"{i+1}. `{u}`" for i, u in enumerate(users)]) if users else "Empty."
        bot.reply_to(message, msg, parse_mode="Markdown")

    elif cmd == '/broadcast':
        groups = load_list(DB_FILE)
        if not groups: return bot.reply_to(message, "❌ No approved groups.")
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
        bot.reply_to(message, f"📢 Broadcast Status:\n✅ Success: {success}\n❌ Failed: {failed}")

    elif cmd == '/tg':
        if not is_subscribed(user_id):
            bot.reply_to(message, "⚠️ Join channels first:", reply_markup=get_join_markup())
            return
        
        is_group_approved = str(message.chat.id) in load_list(DB_FILE)
        is_user_approved = str(user_id) in load_list(USER_APPROVAL_FILE)
        
        if not (is_group_approved or is_user_approved or user_id == OWNER_ID):
            bot.reply_to(message, "🚫 Access Denied (Group/User not approved).")
            return

        usage = load_usage()
        user_id_str = str(user_id)
        is_special = (user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE))
        
        if not is_special:
            if usage.get(user_id_str, 0) >= 15:
                bot.reply_to(message, "❌ Daily limit (15) reached.")
                return
            usage[user_id_str] = usage.get(user_id_str, 0) + 1
            save_usage(usage)
            left_text = f"{15 - usage[user_id_str]}/15"
        else: left_text = "Unlimited"

        term = get_target_id(message)
        if not term: return bot.reply_to(message, "Usage: `/tg <id>` or reply.")
        
        if term in load_list(PROTECTED_DATA_FILE):
            bot.reply_to(message, f"🎯 **TARGET:** `{term}`\n🛡️ **RESULT:** `Protected by Admin`")
            return

        wait_msg = bot.reply_to(message, "🔍 Searching Data...")
        try:
            full_url = f"{API_BASE_URL}{term}"
            response = requests.get(full_url, timeout=20)
            res = response.json()
            
            # Parsing logic based on your screenshot structure
            if res.get('status') is True or 'data' in res:
                data_obj = res.get('data', {})
                name = data_obj.get('display_name', 'N/A')
                p_info = data_obj.get('phone_info', {})
                
                num = p_info.get('number', 'N/A')
                cc = p_info.get('country_code', '')
                country = p_info.get('country', 'N/A')
                uid = data_obj.get('user_id', 'N/A')
                uname = data_obj.get('username', 'N/A')

                ui = (
                    f"🎯 **TARGET:** `{term}`\n"
                    f"👤 **Name:** `{name}`\n"
                    f"📱 **Number:** `{cc}{num}`\n"
                    f"🆔 **TG ID:** `{uid}`\n"
                    f"🔗 **User:** {uname}\n"
                    f"🌍 **Country:** `{country}`\n"
                    f"📊 **Searches Left:** `{left_text}`\n\n"
                    f"🗑️ *Deleting In 30s*"
                )
            else:
                ui = "⚠️ No records found in database."

            dev_markup = InlineKeyboardMarkup().add(InlineKeyboardButton(text="𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/sxdad"))
            final_msg = bot.edit_message_text(ui, message.chat.id, wait_msg.message_id, parse_mode="Markdown", reply_markup=dev_markup)
            threading.Thread(target=delete_later, args=(message.chat.id, final_msg.message_id, 30)).start()
        except Exception as e:
            bot.edit_message_text(f"⚠️ API Error: Check Logs on Railway.", message.chat.id, wait_msg.message_id)
            print(f"DEBUG ERROR: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

if __name__ == "__main__":
    # Robust polling for Railway
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending_updates=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
        
