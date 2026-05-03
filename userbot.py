import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import threading
import time
import json
import re

# --- CONFIG ---
BOT_TOKEN = '8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA'
API_KEY = "j4tnx"
API_BASE_URL = "https://cortex-hosting.gt.tc/"
OWNER_ID = 8442352135

CHANNELS = {
    "1 🚀": {"id": "@snxhub", "url": "https://t.me/snxhub"},
    "2 🚀": {"id": "@snnetwork7", "url": "https://t.me/snnetwork7"},
    "3 🚀": {"id": "@snxhub1", "url": "https://t.me/snxhub1"}
}

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "groups.txt"
USER_APPROVAL_FILE = "approved_users.txt"
UNLIMITED_FILE = "unlimited_users.txt"
PROTECTED_DATA_FILE = "protected_ids.txt"
USAGE_FILE = "usage_data.json"

# ---------- HELPERS ----------
def is_subscribed(user_id):
    if user_id == OWNER_ID:
        return True
    for data in CHANNELS.values():
        try:
            member = bot.get_chat_member(data["id"], user_id)
            if member.status in ['left','kicked','restricted']:
                return False
        except:
            return False
    return True

def get_join_markup():
    m = InlineKeyboardMarkup()
    for name, data in CHANNELS.items():
        m.add(InlineKeyboardButton(f"Join {name}", url=data["url"]))
    m.add(InlineKeyboardButton("Verify ✅", callback_data="verify_user"))
    return m

def load_list(file):
    if os.path.exists(file):
        with open(file) as f:
            return [x.strip() for x in f if x.strip()]
    return []

def save_list(file, items):
    with open(file, "w") as f:
        f.write("\n".join(items))

def load_usage():
    if os.path.exists(USAGE_FILE):
        try:
            return json.load(open(USAGE_FILE))
        except:
            return {}
    return {}

def save_usage(d):
    json.dump(d, open(USAGE_FILE, "w"))

def delete_later(chat, msg, t):
    time.sleep(t)
    try:
        bot.delete_message(chat, msg)
    except:
        pass

# ---------- COMMAND HANDLER ----------
@bot.message_handler(commands=[
    'approvegc','disapprovegc','disapprovegcall','listapprovegc',
    'approvebot','disapprovebot','disapprovebotall','listapprovebot',
    'unprotect','protect','unprotectall','listprotect',
    'unlimited','disunlimited','disunlimitedall','listunlimited',
    'tg','broadcast'
])
def handle(message):

    cmd = message.text.split()[0][1:]
    uid = message.from_user.id
    uid_str = str(uid)

    # ----- OWNER -----
    if uid == OWNER_ID:

        if cmd == "broadcast":
            groups = load_list(DB_FILE)
            ok, fail = 0,0
            for gid in groups:
                try:
                    if message.reply_to_message:
                        bot.copy_message(gid, message.chat.id, message.reply_to_message.message_id)
                    else:
                        txt = message.text.replace('/broadcast','').strip()
                        if txt:
                            bot.send_message(gid, txt)
                    ok += 1
                except:
                    fail += 1
            bot.reply_to(message, f"Sent {ok} | Failed {fail}")

        elif cmd == "approvegc":
            g = load_list(DB_FILE)
            if str(message.chat.id) not in g:
                g.append(str(message.chat.id))
                save_list(DB_FILE, g)
            bot.reply_to(message, "Group Approved")

        elif cmd == "disapprovegc":
            g = load_list(DB_FILE)
            if str(message.chat.id) in g:
                g.remove(str(message.chat.id))
                save_list(DB_FILE, g)
            bot.reply_to(message, "Group Removed")

        elif cmd == "listapprovegc":
            g = load_list(DB_FILE)
            bot.reply_to(message, "\n".join(g) if g else "No groups")

        elif cmd == "listapprovebot":
            u = load_list(USER_APPROVAL_FILE)
            bot.reply_to(message, "\n".join(u) if u else "No users")

        elif cmd == "listprotect":
            p = load_list(PROTECTED_DATA_FILE)
            bot.reply_to(message, "\n".join(p) if p else "No protected")
        
        elif cmd == "listunlimited":
            u = load_list(UNLIMITED_FILE)
            bot.reply_to(message, "\n".join(u) if u else "No unlimited users")

        elif cmd == "disapprovegcall":
            open(DB_FILE,"w").close()
            bot.reply_to(message,"All groups removed")

        elif cmd == "disapprovebotall":
            open(USER_APPROVAL_FILE,"w").close()

        elif cmd == "disunlimitedall":
            open(UNLIMITED_FILE,"w").close()

        elif cmd == "unprotectall":
            open(PROTECTED_DATA_FILE,"w").close()

        elif cmd in ['approvebot','disapprovebot','unlimited','disunlimited','protect','unprotect']:

            args = message.text.split()
            tid = message.reply_to_message.from_user.id if message.reply_to_message else (args[1] if len(args)>1 else None)
            if not tid: return

            file_map = {
                'approvebot': USER_APPROVAL_FILE,
                'disapprovebot': USER_APPROVAL_FILE,
                'unlimited': UNLIMITED_FILE,
                'disunlimited': UNLIMITED_FILE,
                'protect': PROTECTED_DATA_FILE,
                'unprotect': PROTECTED_DATA_FILE
            }

            items = load_list(file_map[cmd])

            if cmd.startswith("dis"):
                if str(tid) in items:
                    items.remove(str(tid))
            else:
                if str(tid) not in items:
                    items.append(str(tid))

            save_list(file_map[cmd], items)
            bot.reply_to(message, f"Done {cmd}")

    # ----- TG SEARCH -----
    if cmd == "tg":

        if not is_subscribed(uid):
            bot.reply_to(message, "Join channels", reply_markup=get_join_markup())
            return

        if not (
            str(message.chat.id) in load_list(DB_FILE)
            or uid_str in load_list(USER_APPROVAL_FILE)
            or uid == OWNER_ID
        ):
            bot.reply_to(message,"Access Denied")
            return

        usage = load_usage()
        unlimited = uid == OWNER_ID or uid_str in load_list(UNLIMITED_FILE)

        if not unlimited:
            if usage.get(uid_str,0) >= 15:
                bot.reply_to(message,"Limit reached")
                return
            usage[uid_str] = usage.get(uid_str,0)+1
            save_usage(usage)
            left = 15-usage[uid_str]
        else:
            left = "Unlimited"

        args = message.text.split()
        term = str(message.reply_to_message.from_user.id) if message.reply_to_message else (args[1] if len(args)>1 else None)

        # CLEAN INPUT
        if term:
            if "term=" in term:
                term = term.split("term=")[-1]
            digits = re.findall(r'\d+', term)
            term = digits[0] if digits else None

        if not term:
            bot.reply_to(message,"Use /tg <id>")
            return

        if term in load_list(PROTECTED_DATA_FILE) and uid != OWNER_ID:
            bot.reply_to(message,"Protected")
            return

        wait = bot.reply_to(message,"Searching...")

        try:
            r = requests.get(
                API_BASE_URL,
                params={'key': API_KEY, 'term': term},
                headers={'User-Agent':'Mozilla/5.0'},
                timeout=15
            )

            txt = r.text.strip()
            if not txt:
                raise Exception("Empty API")

            data = json.loads(txt)

            if str(data.get("status")).lower() == "true":

                d = data.get("data",{})
                p = d.get("phone_info",{})

                msg = (
                    f"👤 {d.get('display_name','N/A')}\n"
                    f"📱 +{p.get('country_code','91')}{p.get('number','N/A')}\n"
                    f"🌍 {p.get('country','India')}\n"
                    f"🎯 {term}\n"
                    f"📊 Left: {left}"
                )

                sent = bot.edit_message_text(msg, message.chat.id, wait.message_id)

                threading.Thread(target=delete_later,args=(message.chat.id,sent.message_id,30)).start()

            else:
                bot.edit_message_text("No Data", message.chat.id, wait.message_id)

        except Exception as e:
            bot.edit_message_text(f"Error: {str(e)}", message.chat.id, wait.message_id)

# VERIFY BUTTON
@bot.callback_query_handler(func=lambda c: c.data=="verify_user")
def verify(c):
    if is_subscribed(c.from_user.id):
        bot.answer_callback_query(c.id,"Verified")
        bot.delete_message(c.message.chat.id, c.message.message_id)
    else:
        bot.answer_callback_query(c.id,"Join first",show_alert=True)

print("Bot Running...")
bot.infinity_polling(skip_pending=True)
