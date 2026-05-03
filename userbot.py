import telebot
import requests

# --- Configuration ---
BOT_TOKEN = "8667746280:AAHJhNUzwJjCx-v1wUFA_SoiCqm9qV3l0EA"
OWNER_ID = 8442352135
API_KEY = "j4tnx"

bot = telebot.TeleBot(BOT_TOKEN)

def fetch_api_data(term):
    url = "https://cortex-hosting.gt.tc/"
    params = {"key": API_KEY, "term": term}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use `/search <number>` to get details.")

@bot.message_handler(commands=['search'])
def handle_search(message):
    # Security: Sirf Owner hi search kar sake (Optional)
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Access Denied! Sirf owner hi iska use kar sakta hai.")
        return

    # Command check: /search 1234567890
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Please provide a number.\nExample: `/search 7513729138`", parse_mode="Markdown")
        return

    search_term = args[1]
    msg = bot.reply_to(message, "🔍 Fetching details...")

    # API Call
    data_res = fetch_api_data(search_term)

    if data_res and data_res.get("status") is True:
        info = data_res.get("data", {})
        p_info = info.get("phone_info", {})

        # Response formatting
        response_text = (
            f"👤 *Display Name:* {info.get('display_name')}\n"
            f"🆔 *Username:* @{info.get('username')}\n"
            f"🔢 *User ID:* `{info.get('user_id')}`\n"
            f"📍 *Country:* {p_info.get('country')}\n"
            f"📞 *Phone:* `{p_info.get('country_code')} {p_info.get('number')}`"
        )
        bot.edit_message_text(response_text, message.chat.id, msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ No data found or API Error.", message.chat.id, msg.message_id)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
    
