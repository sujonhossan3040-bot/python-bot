import telebot
import re
from datetime import datetime, timedelta

# ======================
# 🔹 Bot Token
# ======================
BOT_TOKEN = "8230826781:AAHvHcP1z1x3L1qPIu990w10EA_QmlQnz4Q"  # এখানে আপনার বট টোকেন বসান
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ======================
# 🔹 লিঙ্ক ডিটেকশন
# ======================
link_pattern = re.compile(r"(https?://\S+|t\.me/\S+)", re.IGNORECASE)

# ======================
# 🔹 সব মেসেজ হ্যান্ডলার
# ======================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # যদি মেসেজে লিঙ্ক থাকে
    if link_pattern.search(message.text):
        try:
            # মেসেজ ডিলিট
            bot.delete_message(chat_id, message.message_id)

            # ইউজারকে ১২ ঘণ্টার জন্য মিউট করা
            until_date = datetime.now() + timedelta(hours=12)
            bot.restrict_chat_member(
                chat_id,
                user_id,
                until_date=until_date,
                permissions=telebot.types.ChatPermissions(can_send_messages=False)
            )

            # সতর্কবার্তা মেসেজ
            bot.send_message(
                chat_id,
                f"⚠️ <b>{message.from_user.first_name}</b> "
                f"(ID: <code>{user_id}</code>) লিঙ্ক পাঠানোর কারণে "
                f"<b>12 ঘণ্টার জন্য মেসেজ বন্ধ</b> করা হয়েছে!"
            )

        except Exception as e:
            print(f"❌ Restrict/Delete Error: {e}")

# ======================
# 🔹 Bot চালু
# ======================
print("🤖 Bot is running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
