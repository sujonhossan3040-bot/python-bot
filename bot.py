import os
import telebot
import re
from datetime import datetime, timedelta
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# লিঙ্ক ডিটেকশন
link_pattern = re.compile(r"(https?://\S+|t\.me/\S+)", re.IGNORECASE)

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text and link_pattern.search(message.text):
        try:
            # মেসেজ ডিলিট
            bot.delete_message(chat_id, message.message_id)

            # ইউজারকে ১২ ঘণ্টার জন্য মিউট
            until_date = datetime.utcnow() + timedelta(hours=12)
            perms = types.ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(chat_id, user_id, permissions=perms, until_date=until_date)

            bot.send_message(
                chat_id,
                f"⚠️ <b>{message.from_user.first_name}</b> "
                f"(ID: <code>{user_id}</code>) লিঙ্ক শেয়ার করার কারণে "
                f"<b>12 ঘণ্টার জন্য মিউট</b> করা হয়েছে!"
            )

        except Exception as e:
            print("Error:", e)

print("🤖 Bot is running...")
bot.infinity_polling()