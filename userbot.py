import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAGXQ9hojwUj25auAzakCrFXNKsCwRGMInU'
# Exact URL from your screenshot
API_URL_TEMPLATE = "https://abhigyan-codes-tg-to-number-api.onrender.com/@abhigyan_codes/userid={userid}"
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

    if user_id == OWNER_ID:
        if cmd == '/broadcast':
            groups = load_list(DB_FILE)
            for g in groups:
                try:
                    if message.reply_to_message: bot.copy_message(g, chat_id, message.reply_to_message.message_id)
                    else: bot.send_message(g, " ".join(args[1:]))
                except: pass
            bot.reply_to(message, "✅ Broadcast Sent.")
        elif cmd == '/approvegc':
            if add_to_list(DB_FILE, chat_id): bot.reply_to(message, "✅ Group Approved.")
        elif cmd == '/disapprovegc':
            if remove_from_list(DB_FILE, chat_id): bot.reply_to(message, "🚫 Group Disapproved.")
        elif cmd == '/disapprovegcall':
            clear_file(DB_FILE); bot.reply_to(message, "🗑️ All GC Removed.")
        elif cmd == '/listapprovegc':
            l = load_list(DB_FILE)
            bot.reply_to(message, "🏢 **Approved GCs:**\n" + "\n".join(l) if l else "Empty.")
        elif cmd == '/protect':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if tid and add_to_list(PROTECTED_DATA_FILE, tid): bot.reply_to(message, f"🛡️ {tid} Protected.")
        elif cmd == '/unprotect':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if tid and remove_from_list(PROTECTED_DATA_FILE, tid): bot.reply_to(message, f"🔓 {tid} Unprotected.")
        elif cmd == '/unprotectall':
            clear_file(PROTECTED_DATA_FILE); bot.reply_to(message, "🗑️ All Unprotected.")
        elif cmd == '/listprotect':
            l = load_list(PROTECTED_DATA_FILE)
            bot.reply_to(message, "🛡️ **Protected IDs:**\n" + "\n".join(l) if l else "Empty.")
        elif cmd == '/unlimited':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if tid and add_to_list(UNLIMITED_FILE, tid): bot.reply_to(message, f"🚀 {tid} Unlimited.")
        elif cmd == '/disunlimited':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if tid and remove_from_list(UNLIMITED_FILE, tid): bot.reply_to(message, f"📉 {tid} Removed.")
        elif cmd == '/disunlimitedall':
            clear_file(UNLIMITED_FILE); bot.reply_to(message, "🗑️ Unlimited List Cleared.")
        elif cmd == '/listunlimited':
            l = load_list(UNLIMITED_FILE)
            bot.reply_to(message, "🚀 **Unlimited Users:**\n" + "\n".join(l) if l else "Empty.")
        elif cmd == '/approvebot':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if tid and add_to_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"👤 {tid} Approved.")
        elif cmd == '/disapprovebot':
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if tid and remove_from_list(USER_APPROVAL_FILE, tid): bot.reply_to(message, f"🚫 {tid} Disapproved.")
        elif cmd == '/disapprovebotall':
            clear_file(USER_APPROVAL_FILE); bot.reply_to(message, "🗑️ Personal List Cleared.")
        elif cmd == '/listapprovebot':
            l = load_list(USER_APPROVAL_FILE)
            bot.reply_to(message, "👤 **Personal Users:**\n" + "\n".join(l) if l else "Empty.")

    # --- SEARCH COMMAND (/tg) ---
    if cmd == '/tg':
        if not is_subscribed(user_id):
            return bot.reply_to(message, "⚠️ Join Channels First:", reply_markup=get_join_markup())

        if not (str(chat_id) in load_list(DB_FILE) or str(user_id) in load_list(USER_APPROVAL_FILE) or user_id == OWNER_ID):
            return bot.reply_to(message, "🚫 Group or User not approved.")

        today = time.strftime("%Y-%m-%d")
        usage = load_usage()
        uid_str = str(user_id)
        
        if user_id != OWNER_ID and uid_str not in load_list(UNLIMITED_FILE):
            user_data = usage.get(uid_str, {"date": today, "count": 0})
            if user_data["date"] != today: user_data = {"date": today, "count": 0}
            if user_data["count"] >= 8:
                return bot.reply_to(message, "🚫 Daily Limit Exceeded!")
            user_data["count"] += 1
            usage[uid_str] = user_data
            save_usage(usage)
            current_count = f"{user_data['count']}/8"
        else:
            current_count = "Unlimited"

        target = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args)>1 else None)
        if not target: return bot.reply_to(message, "Usage: `/tg {id}` or reply.")

        if target in load_list(PROTECTED_DATA_FILE) and user_id != OWNER_ID:
            return bot.reply_to(message, f"🎯 **Target:** `{target}`\n🛡️ **Result:** `Protected`")

        wait = bot.reply_to(message, "🔍 Searching API... Please wait.")
        try:
            final_url = API_URL_TEMPLATE.format(userid=target)
            response = requests.get(final_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            res = response.json()
            
            # --- CRITICAL FIX START ---
            # Aapke screenshot mein 'success' direct JSON root mein hai
            success_status = res.get("success")
            
            # Hum check karenge ki success true hai (chahe wo string ho ya boolean)
            if str(success_status).lower() == "true":
                # Data nikalna (Screenshot ke hisaab se direct root mein hain ye keys)
                num = res.get("number", "Not Found")
                country = res.get("country", "N/A")
                code = res.get("country_code", "N/A")
                
                # Agar root mein nahi mila, to 'result' key ke andar check karo (backup plan)
                if num == "Not Found" and isinstance(res.get("result"), dict):
                    num = res["result"].get("number", "Not Found")
                    country = res["result"].get("country", "N/A")
                    code = res["result"].get("country_code", "N/A")

                ui = (f"✨ **SN X SEARCH RESULTS** ✨\n━━━━━━━━━━━━━━━\n"
                      f"👤 **User ID:** `{target}`\n"
                      f"📞 **Number:** `{num}`\n"
                      f"🌍 **Country:** {country} ({code})\n"
                      f"📊 **Usage Today:** {current_count}\n"
                      f"━━━━━━━━━━━━━━━\n⏳ *Deleting both in 30s*")
            else: 
                msg = res.get("msg", "No data found")
                ui = f"❌ **No Data Found** for `{target}`.\nReason: `{msg}`"
            # --- CRITICAL FIX END ---

            btn = InlineKeyboardMarkup().add(InlineKeyboardButton("𝐒𝐍 𝐗 𝐃𝐀𝐃 🦁", url="https://t.me/snxdad"))
            final = bot.edit_message_text(ui, chat_id, wait.message_id, parse_mode="Markdown", reply_markup=btn)
            threading.Thread(target=auto_delete_task, args=(chat_id, [message.message_id, final.message_id], 30)).start()
        except Exception as e:
            bot.edit_message_text(f"⚠️ API Connection Error.", chat_id, wait.message_id)
            
@bot.callback_query_handler(func=lambda call: call.data == "verify_user")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else: bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

if __name__ == "__main__":
    print("Bot is running...")
    bot.delete_webhook()
    bot.infinity_polling(skip_pending=True)
                                                                                          
