import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# --- CONFIGURATION ---
API_URL = "https://tg-num-api.onrender.com/tg?id="
BOT_TOKEN = "8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA"
OWNER_ID = 8442352135

FORCE_JOIN_CHANNELS = {
    "1 🚀": {"id": "@snxhub", "url": "https://t.me/snxhub"},
    "2 🚀": {"id": "@snnetwork7", "url": "https://t.me/snnetwork7"},
    "3 🚀": {"id": "@snxhub1", "url": "https://t.me/snxhub1"}
}

# --- DATABASE ---
approved_gcs = {}
protected_users = set()  
personal_users = set()

# --- FORCE JOIN CHECKER ---
async def is_subscribed(bot, user_id):
    for data in FORCE_JOIN_CHANNELS.values():
        try:
            member = await bot.get_chat_member(data['id'], user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

# --- VERIFY BUTTON HANDLER ---
async def verify_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if await is_subscribed(context.bot, user_id):
        await query.answer("✅ Verification Successful! Ab aap bot use kar sakte hain.", show_alert=True)
        await query.message.delete()
    else:
        await query.answer("❌ Aapne abhi tak saare channels join nahi kiye hain!", show_alert=True)

# --- TG COMMAND WITH SEARCHING STATUS & AUTO DELETE ---
async def tg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # 1. Force Join Check
    if not await is_subscribed(context.bot, user_id) and user_id != OWNER_ID:
        keyboard = [[InlineKeyboardButton(n, url=d['url'])] for n, d in FORCE_JOIN_CHANNELS.items()]
        keyboard.append([InlineKeyboardButton("Verify ✅", callback_data="verify_user")])
        return await update.message.reply_text("❌ **Access Denied!**\nBot use karne ke liye neeche diye gaye channels join karein aur Verify par click karein.", 
                                               reply_markup=InlineKeyboardMarkup(keyboard))

    # 2. Access Control
    if not (user_id == OWNER_ID or user_id in personal_users or chat_id in approved_gcs):
        return await update.message.reply_text("⚠️ No access. Group approved nahi hai ya personal access nahi hai.")

    # 3. ID Detection
    target_id = None
    if update.message.reply_to_message:
        target_id = str(update.message.reply_to_message.from_user.id)
    elif context.args:
        target_id = context.args[0]
    else:
        return await update.message.reply_text("Usage: `/tg {id}` ya user ko reply karein.")

    if int(target_id) in protected_users and user_id != OWNER_ID:
        return await update.message.reply_text("🛡️ Yeh user protected hai.")

    # 4. Searching Message
    searching_msg = await update.message.reply_text("🔍 **Searching... Please wait.**")

    try:
        response = requests.get(f"{API_URL}{target_id}").json()
        
        if response.get("success"):
            text = (
                f"✨ **Search Results Found** ✨\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 **User ID:** `{response.get('user_id')}`\n"
                f"📞 **Number:** `{response.get('number')}`\n"
                f"🌍 **Country:** {response.get('Country')} ({response.get('Country Code')})\n"
                f"🛠️ **Dev:** {response.get('dev')}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"⏳ *Auto-delete in 30s*"
            )
        else:
            text = "❌ No data found for this ID."

        btn = [[InlineKeyboardButton("𝐒𝐍 𝐗 𝐃𝐀𝐃🦁", url="https://t.me/snxdad")]]
        
        # Edit searching message with result
        await searching_msg.edit_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

        # 5. Auto Delete Logic
        await asyncio.sleep(30)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=searching_msg.message_id)
            await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        except: pass

    except Exception:
        await searching_msg.edit_text("❌ API connection error.")

# --- OWNER CMDS (LISTED IN PREVIOUS RESPONSE) ---
async def owner_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    cmd = update.message.text.split()[0].lower()
    arg = context.args[0] if context.args else None
    
    if cmd == "/approvegc": approved_gcs[update.effective_chat.id] = update.effective_chat.title
    elif cmd == "/protect" and arg: protected_users.add(int(arg))
    elif cmd == "/approvebot" and arg: personal_users.add(int(arg))
    
    await update.message.reply_text("✅ Done.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("tg", tg_command))
    app.add_handler(CallbackQueryHandler(verify_button, pattern="verify_user"))
    
    owner_list = ["approvegc", "disapprovegc", "protect", "unprotect", "approvebot"]
    app.add_handler(CommandHandler(owner_list, owner_manage))
    
    print("Bot is Live with Verify System...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
