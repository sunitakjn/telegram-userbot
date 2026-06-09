import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAGXQ9hojwUj25auAzakCrFXNKsCwRGMInU'
API_URL = "https://shivam-ultra-api.vercel.app/tg"
API_KEY = "Y"
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
    items = load_list(file); it = str(item)
    if it in items:
        items.remove(it); save_list(file, items); return True
    return False

def clear_file(file):
    with open(file, "w") as f: f.truncate(0)

def load_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_usage(data):
    with open(USAGE_FILE, "w") as f: json.dump(data, f)

def auto_delete_task(chat_id, msg_ids, delay):
    time.sleep(delay)
    for mid in msg_ids:
        try: bot.delete_message(chat_id, mid)
        except: pass

# --- MAIN COMMAND HANDLER ---
@bot.message_handler(commands=[
    'approvegc', 'disapprovegc', 'disapprovegcall', 'listapprovegc', 
    'approvebot', 'disapprovebot', 'disapprovebotall', 'listapprovebot', 
    'unprotect', 'protect', 'unprotectall', 'listprotect', 
    'unlimited', 'disunlimited', 'disunlimitedall', 'listunlimited', 'tg', 'broadcast'
])
def handle_commands(message):
    cmd = message.text.split()[0].split('@')[0].lower()
    user_id = message.from_user.id
    chat_id = message.chat.id
    args = message.text.split()

    owner_commands = [
        '/broadcast', '/approvegc', '/disapprovegc', '/disapprovegcall', '/listapprovegc', 
        '/approvebot', '/disapprovebot', '/disapprovebotall', '/listapprovebot', 
        '/unprotect', '/protect', '/unprotectall', '/listprotect', 
        '/unlimited', '/disunlimited', '/disunlimitedall', '/listunlimited'
    ]

    # OWNER VALIDATION CHECK
    if cmd in owner_commands and user_id != OWNER_ID:
        return bot.reply_to(message, "🚫 Only the bot Owner can use this command.")

    # --- OWNER LOGIC EXECUTION ---
    if cmd == '/broadcast':
        groups = load_list(DB_FILE)
        success = 0
        failed = 0
        success_list = []
        failed_list = []

        if len(args) < 2 and not message.reply_to_message:
            return bot.reply_to(message, "Usage: `/broadcast {message}` or reply to a message.")

        for g in groups:
            try:
                if message.reply_to_message:
                    bot.copy_message(int(g), chat_id, message.reply_to_message.message_id)
                else:
                    bot.send_message(int(g), " ".join(args[1:]))
                success += 1
                try:
                    chat = bot.get_chat(int(g))
                    success_list.append(chat.title)
                except:
                    success_list.append(str(g))
            except:
                failed += 1
                failed_list.append(str(g))

        report = (
            f"📢 Broadcast Report\n\n"
            f"✅ Success : {success}\n"
            f"❌ Failed : {failed}\n"
            f"📂 Total : {len(groups)}\n\n"
        )
        if success_list:
            report += "✅ Sent To:\n" + "\n".join([f"• {x}" for x in success_list[:30]]) + "\n\n"
        if failed_list:
            report += "❌ Failed GCs:\n" + "\n".join([f"• {x}" for x in failed_list[:30]])
        bot.reply_to(message, report)

    elif cmd == '/approvegc':
        if add_to_list(DB_FILE, chat_id): bot.reply_to(message, "✅ Group Approved.")
    elif cmd == '/disapprovegc':
        if remove_from_list(DB_FILE, chat_id): bot.reply_to(message, "🚫 Group Disapproved.")
    elif cmd == '/disapprovegcall':
        clear_file(DB_FILE); bot.reply_to(message, "🗑️ All GC Removed.")
    elif cmd == '/listapprovegc':
        groups = load_list(DB_FILE)
        if not groups: return bot.reply_to(message, "No Approved Groups.")
        text = "🏢 Approved Groups\n\n"
        for gid in groups:
            try:
                chat = bot.get_chat(int(gid))
                text += f"📌 Name : {chat.title}\n🆔 ID : {gid}\n\n"
            except:
                text += f"📌 Name : Unknown\n🆔 ID : {gid}\n\n"
        bot.reply_to(message, text)

    elif cmd == '/protect':
        tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
        if tid and add_to_list(PROTECTED_DATA_FILE, tid): bot.reply_to(message, f"🛡️ {tid} Protected.")
    elif cmd == '/unprotect':
        tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
        if tid and remove_from_list(PROTECTED_DATA_FILE, tid): bot.reply_to(message, f"🔓 {tid} Unprotected.")
    elif cmd == '/unprotectall':
        clear_file(PROTECTED_DATA_FILE); bot.reply_to(message, "🗑️ All Unprotected.")
    elif cmd == '/listprotect':
        users = load_list(PROTECTED_DATA_FILE)
        if not users: return bot.reply_to(message, "No Protected Users.")
        text = "🛡 Protected Users\n\n"
        for uid in users:
            try:
                user = bot.get_chat(int(uid))
                username = f"@{user.username}" if user.username else "No Username"
                text += f"👤 Name : {user.first_name}\n🔗 Username : {username}\n🆔 ID : {uid}\n\n"
            except: text += f"🆔 ID : {uid}\n\n"
        bot.reply_to(message, text)

    elif cmd == '/unlimited':
        tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
        if tid and add_to_list(UNLIMITED_FILE, tid): bot.reply_to(message, f"🚀 {tid} Unlimited.")
    elif cmd == '/disunlimited':
        tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
        if tid and remove_from_list(UNLIMITED_FILE, tid): bot.reply_to(message, f"📉 {tid} Removed.")
    elif cmd == '/disunlimitedall':
        clear_file(UNLIMITED_FILE); bot.reply_to(message, "🗑️ Unlimited List Cleared.")
    elif cmd == '/listunlimited':
        users = load_list(UNLIMITED_FILE)
        if not users: return bot.reply_to(message, "No Unlimited Users.")
        text = "🚀 Unlimited Users\n\n"
        for uid in users:
            try:
                user = bot.get_chat(int(uid))
                username = f"@{user.username}" if user.username else "No Username"
                text += f"👤 Name : {user.first_name}\n🔗 Username : {username}\n🆔 ID : {uid}\n\n"
            except: text += f"🆔 ID : {uid}\n\n"
        bot.reply_to(message, text)

    elif cmd == '/approvebot':
        tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
        if tid and add_to_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"👤 {tid} Approved.")
    elif cmd == '/disapprovebot':
        tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
        if tid and remove_from_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"🚫 {tid} Disapproved.")
    elif cmd == '/disapprovebotall':
        clear_file(USER_APPROVAL_FILE); bot.reply_to(message, "🗑️ Personal List Cleared.")
    elif cmd == '/listapprovebot':
        users = load_list(USER_APPROVAL_FILE)
        if not users: return bot.reply_to(message, "No Approved Users.")
        text = "👤 Approved Users\n\n"
        for uid in users:
            try:
                user = bot.get_chat(int(uid))
                username = f"@{user.username}" if user.username else "No Username"
                text += f"👤 Name : {user.first_name}\n🔗 Username : {username}\n🆔 ID : {uid}\n\n"
            except: text += f"🆔 ID : {uid}\n\n"
        bot.reply_to(message, text)

    # --- SEARCH COMMAND (/tg) ---
    elif cmd == '/tg':
        if not is_subscribed(user_id):
            return bot.reply_to(message, "⚠️ Join Channels First:", reply_markup=get_join_markup())

        if not (str(chat_id) in load_list(DB_FILE) or str(user_id) in load_list(USER_APPROVAL_FILE) or user_id == OWNER_ID):
            return bot.reply_to(message, "🚫 Group Or User Not Approved Contact @SxDAD ✅.")

        # TARGET DETECTION (Reply / Username / ID)
        target = None
        if message.reply_to_message:
            target = str(message.reply_to_message.from_user.id)
        elif len(args) > 1:
            target = args[1].strip()

        if not target: 
            return bot.reply_to(message, "❌ **Usage:** `/tg {id}` ya `/tg @username` ya kisi user ke message par reply karein.")

        # USERNAME CONVERSION LOGIC
        if target.startswith('@'):
            wait_resolve = bot.reply_to(message, "🔍 Username se ID convert ki ja rahi hai...")
            try:
                chat_info = bot.get_chat(target)
                target = str(chat_info.id)
                bot.delete_message(chat_id, wait_resolve.message_id)
            except Exception as e:
                return bot.edit_message_text("❌ Username ki ID nahi mil saki.", chat_id, wait_resolve.message_id)

        # --- LIMIT CHECK LOGIC ---
        today = time.strftime("%Y-%m-%d")
        usage = load_usage()
        uid_str = str(user_id)
        
        if user_id != OWNER_ID and uid_str not in load_list(UNLIMITED_FILE):
            user_data = usage.get(uid_str, {"date": today, "count": 0})
            if user_data["date"] != today:
                user_data = {"date": today, "count": 0}
            
            if user_data["count"] >= 10:
                return bot.reply_to(message, "🚫 Daily Limit Exceeded! You can only search 10 times per day.")
            
            user_data["count"] += 1
            usage[uid_str] = user_data
            save_usage(usage)
            current_count = f"{user_data['count']}/10"
        else:
            current_count = "Unlimited"

        if target in load_list(PROTECTED_DATA_FILE) and user_id != OWNER_ID:
            return bot.reply_to(message, f"🎯 **Target:** `{target}`\n🛡️ **Result:** `❌ No Data Found`")

        wait = bot.reply_to(message, "🔍 Searching API... Please wait.")
        try:
            # API Request
            res = requests.get(f"{API_URL}?id={target}", timeout=10).json()
            
            # PARSING LOGIC UPDATED BASED ON SCREENSHOT
            if res.get("success") and "data" in res:
                api_data = res.get("data", {})
                
                tg_id = api_data.get("tg_id", "N/A")
                number = api_data.get("number", "N/A")
                country = api_data.get("country", "N/A")
                country_code = api_data.get("country_code", "N/A")

                ui = (f"✨ **SN X OSINT RESULTS** ✨\n━━━━━━━━━━━━━━━\n"
                      f"👤 **User ID:** `{tg_id}`\n"
                      f"📞 **Number:** `{number}`\n"
                      f"🌍 **Country:** {country} ({country_code})\n"
                      f"📊 **Usage Today:** {current_count}\n"
                      f"━━━━━━━━━━━━━━━\n⏳ *Deleting both in 30s*")
            else: 
                ui = f"❌ No Data Found `{target}`."

            btn = InlineKeyboardMarkup().add(InlineKeyboardButton("𝐒𝐍 𝐗 𝐃𝐀𝐃", url="https://t.me/snxdad"))
            final = bot.edit_message_text(ui, chat_id, wait.message_id, parse_mode="Markdown", reply_markup=btn)
            
            threading.Thread(target=auto_delete_task, args=(chat_id, [message.message_id, final.message_id], 30)).start()
        except Exception as err:
            bot.edit_message_text(f"⚠️ API Connection Error.", chat_id, wait.message_id)
            
@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified !")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else: 
        bot.answer_callback_query(call.id, "❌ Join All Channels First !", show_alert=True)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
                                          
