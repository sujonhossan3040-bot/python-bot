import telebot
import re
from datetime import datetime, timedelta

# ======================
# 🔹 Bot Token
# ======================
BOT_TOKEN = "8230826781:AAHvHcP1z1x3L1qPIu990w10EA_QmlQnz4Q"  # এখানে তোমার বট টোকেন বসাও
bot = telebot.TeleBot(BOT_TOKEN)

# ======================
# 🔹 লিঙ্ক ডিটেকশন
# ======================
link_pattern = re.compile(r"(https?://\S+|t\.me/\S+)")

# ======================
# 🔹 নতুন ইউজার ওয়েলকাম
# ======================
@bot.message_handler(content_types=['new_chat_members'])
def welcome_user(message):
    for user in message.new_chat_members:
        bot.send_message(
            message.chat.id,
            f"👋 স্বাগতম {user.first_name or 'User'}!\n"
            f"🆔 User ID: {user.id}\n"
            f"💬 Group: {message.chat.title}"
        )

# ======================
# 🔹 সব মেসেজ হ্যান্ডলার
# ======================
@bot.message_handler(content_types=['text'])
def handle_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # যদি মেসেজে লিঙ্ক থাকে
    if link_pattern.search(message.text):
        try:
            bot.delete_message(chat_id, message.message_id)

            until_date = datetime.now() + timedelta(hours=12)
            bot.restrict_chat_member(
                chat_id,
                user_id,
                until_date=until_date,
                can_send_messages=False
            )

            bot.send_message(
                chat_id,
                f"⚠️ {message.from_user.first_name} ({user_id}) ১২ ঘন্টার জন্য মেসেজ পাঠানোর থেকে ব্যান হলো (লিঙ্ক পাঠানোর কারণে)!"
            )

        except Exception as e:
            print("Error:", e)

# ======================
# 🔹 Bot চালু
# ======================
print("🤖 Bot is running...")
bot.infinity_polling()
