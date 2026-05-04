import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- CONFIGURATION ---
API_URL = "https://tg-num-api.onrender.com/tg?id="
BOT_TOKEN = "8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA"
OWNER_ID = 8442352135

FORCE_JOIN_CHANNELS = {
    "1 🚀": {"id": "@snxhub", "url": "https://t.me/snxhub"},
    "2 🚀": {"id": "@snnetwork7", "url": "https://t.me/snnetwork7"},
    "3 🚀": {"id": "@snxhub1", "url": "https://t.me/snxhub1"}
}

# --- DATABASE (In-Memory) ---
approved_gcs = {}
protected_users = set()  
unlimited_users = set()
personal_users = set()

# --- HELPERS ---
def is_owner(user_id):
    return user_id == OWNER_ID

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_owner(user_id): return True
    for data in FORCE_JOIN_CHANNELS.values():
        try:
            member = await context.bot.get_chat_member(data['id'], user_id)
            if member.status in ['left', 'kicked']: raise Exception()
        except:
            keyboard = [[InlineKeyboardButton(n, url=d['url'])] for n, d in FORCE_JOIN_CHANNELS.items()]
            await update.message.reply_text("❌ **Join our channels first!**", reply_markup=InlineKeyboardMarkup(keyboard))
            return False
    return True

# --- CLEAN UI & AUTO-DELETE LOGIC ---
async def tg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_force_join(update, context): return
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not (is_owner(user_id) or user_id in personal_users or chat_id in approved_gcs):
        return await update.message.reply_text("⚠️ No access.")

    target_id = None
    if update.message.reply_to_message:
        target_id = str(update.message.reply_to_message.from_user.id)
    elif context.args:
        target_id = context.args[0]
    else:
        return await update.message.reply_text("Usage: `/tg {id}` or reply to a user.")

    if int(target_id) in protected_users and not is_owner(user_id):
        return await update.message.reply_text("🛡️ User Protected.")

    try:
        response = requests.get(f"{API_URL}{target_id}").json()
        
        if response.get("success"):
            # --- CLEAN UI DESIGN ---
            text = (
                f"✨ **Search Results Found** ✨\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 **User ID:** `{response.get('user_id')}`\n"
                f"📞 **Number:** `{response.get('number')}`\n"
                f"🌍 **Country:** {response.get('Country')} ({response.get('Country Code')})\n"
                f"🛠️ **Dev:** {response.get('dev')}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏳ *This message will delete in 30s*"
            )
        else:
            text = "❌ No data found for this ID."

        btn = [[InlineKeyboardButton("𝐒𝐍 𝐗 𝐃𝐀𝐃🦁", url="https://t.me/snxdad")]]
        sent_msg = await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

        # --- AUTO DELETE TIMER (30 SECONDS) ---
        await asyncio.sleep(30)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=sent_msg.message_id)
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        except: pass

    except Exception:
        await update.message.reply_text("❌ API Error or ID Invalid.")

# --- OWNER MANAGEMENT COMMANDS ---
async def owner_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    cmd = update.message.text.split()[0].lower()
    arg = context.args[0] if context.args else None
    
    msg = "✅ Action Completed."
    if cmd == "/approvegc": approved_gcs[update.effective_chat.id] = update.effective_chat.title
    elif cmd == "/disapprovegc": approved_gcs.pop(update.effective_chat.id, None)
    elif cmd == "/disapprovegcall": approved_gcs.clear()
    elif cmd == "/listapprovegc": msg = f"Approved GCs: {list(approved_gcs.values())}"
    elif cmd == "/protect" and arg: protected_users.add(int(arg))
    elif cmd == "/unprotect" and arg: protected_users.discard(int(arg))
    elif cmd == "/unprotectall": protected_users.clear()
    elif cmd == "/listprotect": msg = f"Protected IDs: {list(protected_users)}"
    elif cmd == "/unlimited" and arg: unlimited_users.add(int(arg))
    elif cmd == "/listunlimited": msg = f"Unlimited IDs: {list(unlimited_users)}"
    elif cmd == "/approvebot" and arg: personal_users.add(int(arg))
    
    await update.message.reply_text(msg)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or not context.args: return
    text = " ".join(context.args)
    for gid in approved_gcs:
        try: await context.bot.send_message(gid, f"📢 **BROADCAST**\n\n{text}")
        except: pass
    await update.message.reply_text("Sent.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("tg", tg_command))
    owner_cmds = ["approvegc", "disapprovegc", "disapprovegcall", "listapprovegc", "protect", "unprotect", "unprotectall", "listprotect", "unlimited", "listunlimited", "approvebot"]
    app.add_handler(CommandHandler(owner_cmds, owner_manage))
    app.add_handler(CommandHandler("broadcast", broadcast))
    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
