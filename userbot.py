import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json
import re

# --- CONFIGURATION ---
BOT_TOKEN = '8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA'
API_KEY = "j4tnx"
API_BASE_URL = "https://cortex-hosting.gt.tc/"
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
    if user_id == OWNER_ID:
        return True
    for data in CHANNELS.values():
        try:
            member = bot.get_chat_member(data["id"], user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                return False
        except:
            return False
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
            return [x.strip() for x in f if x.strip()]
    return []

def save_list(file, items):
    with open(file, "w") as f:
        for i in items:
            f.write(i + "\n")

def load_usage():
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_usage(data):
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)

def delete_later(chat_id, msg_id, delay):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, msg_id)
    except:
        pass

# --- COMMAND HANDLER ---
@bot.message_handler(commands=[
    'approvegc','disapprovegc','disapprovegcall','listapprovegc',
    'approvebot','disapprovebot','disapprovebotall','listapprovebot',
    'unprotect','protect','unprotectall','listprotect',
    'unlimited','disunlimited','disunlimitedall','listunlimited',
    'tg','broadcast'
])
def handle_commands(message):
    cmd = message.text.split()[0].split('@')[0].lower()[1:]
    user_id = message.from_user.id
    user_id_str = str(user_id)

    # ---------------- OWNER ----------------
    if user_id == OWNER_ID:

        if cmd == 'broadcast':
            groups = load_list(DB_FILE)
            success, failed = 0, 0
            for gid in groups:
                try:
                    if message.reply_to_message:
                        bot.copy_message(gid, message.chat.id, message.reply_to_message.message_id)
                    else:
                        text = message.text.replace('/broadcast', '').strip()
                        if text:
                            bot.send_message(gid, text)
                    success += 1
                except:
                    failed += 1
            bot.reply_to(message, f"✅ {success} Sent | ❌ {failed} Failed")

        elif cmd == 'disunlimitedall':
            open(UNLIMITED_FILE, "w").close()
            bot.reply_to(message, "Unlimited cleared")

        elif cmd == 'unprotectall':
            open(PROTECTED_DATA_FILE, "w").close()
            bot.reply_to(message, "Protection cleared")

        elif cmd == 'disapprovegcall':
            open(DB_FILE, "w").close()
            bot.reply_to(message, "All groups removed")

        elif cmd == 'disapprovebotall':
            open(USER_APPROVAL_FILE, "w").close()
            bot.reply_to(message, "Users removed")

        elif cmd in ['approvebot','disapprovebot','unlimited','disunlimited','protect','unprotect']:
            args = message.text.split()
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args) > 1 else None)
            if not tid:
                return

            file_map = {
                'approvebot': USER_APPROVAL_FILE,
                'disapprovebot': USER_APPROVAL_FILE,
                'unlimited': UNLIMITED_FILE,
                'disunlimited': UNLIMITED_FILE,
                'protect': PROTECTED_DATA_FILE,
                'unprotect': PROTECTED_DATA_FILE
            }

            items = load_list(file_map[cmd])

            if cmd.startswith('dis'):
                if str(tid) in items:
                    items.remove(str(tid))
            else:
                if str(tid) not in items:
                    items.append(str(tid))

            save_list(file_map[cmd], items)
            bot.reply_to(message, f"Done: {cmd} {tid}")

        elif cmd == 'approvegc':
            items = load_list(DB_FILE)
            if str(message.chat.id) not in items:
                items.append(str(message.chat.id))
                save_list(DB_FILE, items)
            bot.reply_to(message, "Group Approved")

    # ---------------- TG SEARCH ----------------
    if cmd == 'tg':

        if not is_subscribed(user_id):
            bot.reply_to(message, "Join channels first", reply_markup=get_join_markup())
            return

        if not (
            str(message.chat.id) in load_list(DB_FILE)
            or user_id_str in load_list(USER_APPROVAL_FILE)
            or user_id == OWNER_ID
        ):
            bot.reply_to(message, "Access Denied")
            return

        usage = load_usage()
        is_unlimited = user_id == OWNER_ID or user_id_str in load_list(UNLIMITED_FILE)

        if not is_unlimited:
            if usage.get(user_id_str, 0) >= 15:
                bot.reply_to(message, "Daily limit reached")
                return
            usage[user_id_str] = usage.get(user_id_str, 0) + 1
            save_usage(usage)
            left = 15 - usage[user_id_str]
        else:
            left = "Unlimited"

        args = message.text.split()
        term = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args) > 1 else None)

        # 🔥 CLEAN INPUT
        if term:
            if "term=" in term:
                term = term.split("term=")[-1]
            digits = re.findall(r'\d+', term)
            term = digits[0] if digits else None

        if not term:
            bot.reply_to(message, "Use: /tg <id>")
            return

        if term in load_list(PROTECTED_DATA_FILE) and user_id != OWNER_ID:
            bot.reply_to(message, "Protected Target")
            return

        wait = bot.reply_to(message, "Searching...")

        try:
response = requests.get(
    API_BASE_URL,
    params={'key': API_KEY, 'term': term},
    headers={
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'application/json'
    },
    timeout=15
)

if response.status_code != 200:
    raise Exception(f"HTTP {response.status_code}")

text = response.text.strip()
print("API RAW:", text)  # debug console me dikhega

if not text:
    raise Exception("Empty API response")

try:
    data = json.loads(text)
except:
    raise Exception("Invalid JSON from API")

if response.status_code != 200:
    raise Exception(f"HTTP {response.status_code}")

text = response.text.strip()
print("API RAW:", text)  # debug console me dikhega

if not text:
    raise Exception("Empty API response")

try:
    data = json.loads(text)
except:
    raise Exception("Invalid JSON from API")

if response.status_code != 200:
    raise Exception(f"HTTP {response.status_code}")

text = response.text.strip()
print("API RAW:", text)  # debug console me dikhega

if not text:
    raise Exception("Empty API response")

try:
    data = json.loads(text)
except:
    raise Exception("Invalid JSON from API")

            data = response.json()

            if str(data.get("status")).lower() == "true":

                d = data.get("data", {})
                p = d.get("phone_info", {})

                msg = (
                    f"👤 Name: {d.get('display_name','N/A')}\n"
                    f"📱 Number: +{p.get('country_code','91')}{p.get('number','N/A')}\n"
                    f"🌍 Country: {p.get('country','India')}\n"
                    f"🎯 Target: {term}\n"
                    f"📊 Left: {left}"
                )

                sent = bot.edit_message_text(msg, message.chat.id, wait.message_id)

                threading.Thread(target=delete_later, args=(message.chat.id, sent.message_id, 30)).start()

            else:
                bot.edit_message_text("Data Not Found", message.chat.id, wait.message_id)

        except Exception as e:
            bot.edit_message_text(f"Error: {str(e)}", message.chat.id, wait.message_id)

# --- VERIFY BUTTON ---
@bot.callback_query_handler(func=lambda c: c.data == "verify_user")
def verify(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "Verified")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Join first", show_alert=True)

# --- START ---
print("Bot Running...")
bot.infinity_polling(skip_pending=True)
