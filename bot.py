import telebot
import threading
import time
import re
from datetime import datetime, timedelta

# ======================
# 🔹 Bot Token
# ======================
BOT_TOKEN = "8230826781:AAHvHcP1z1x3L1qPIu990w10EA_QmlQnz4Q"  # এখানে আপনার বট টোকেন বসান
bot = telebot.TeleBot(BOT_TOKEN)

# ======================
# 🔹 লিঙ্ক ডিটেকশন
# ======================
link_pattern = re.compile(r"(https?://\S+|t\.me/\S+)")

# 🔹 ইউজার লিঙ্ক কাউন্ট ট্র্যাকিং
user_links = {}

# ======================
# 🔹 মেসেজ ডিলিট ফাংশন
# ======================
def schedule_delete(chat_id, message_id, delay=300):
    """মেসেজ ডিলিট করার ফাংশন (delay সেকেন্ডে)"""
    def delete_message():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print("Error:", e)
    threading.Thread(target=delete_message).start()

# ======================
# 🔹 নতুন ইউজার ওয়েলকাম
# ======================
@bot.message_handler(content_types=['new_chat_members'])
def welcome_user(message):
    for user in message.new_chat_members:
        notice = bot.send_message(
            message.chat.id,
            f"👋 স্বাগতম {user.first_name or 'User'}!\n"
            f"🆔 User ID: {user.id}\n"
            f"💬 Group: {message.chat.title}",
            parse_mode="Markdown"
        )
        schedule_delete(message.chat.id, notice.message_id, delay=600)  # 10 মিনিট পরে ডিলিট

# ======================
# 🔹 /job কমান্ড
# ======================
@bot.message_handler(commands=['job'])
def job_command(message):
    reply = bot.reply_to(message, "💼 আপনার জব অ্যাপ্লিকেশন রেকর্ড হলো।")
    schedule_delete(message.chat.id, reply.message_id, delay=600)  # 10 মিনিট পরে ডিলিট

# ======================
# 🔹 সব মেসেজ হ্যান্ডলার
# ======================
@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation'])
def handle_messages(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # লিঙ্ক হলে সাথে সাথে ডিলিট + কাউন্ট
    if message.content_type == 'text' and link_pattern.search(message.text):
        try:
            bot.delete_message(chat_id, message.message_id)

            # ইউজার লিঙ্ক কাউন্ট বাড়ানো
            user_links[user_id] = user_links.get(user_id, 0) + 1
            print(f"User {user_id} link count: {user_links[user_id]}")

            # যদি 5 বারের বেশি লিঙ্ক শেয়ার করে
            if user_links[user_id] > 5:
                until_date = datetime.now() + timedelta(hours=12)
                bot.restrict_chat_member(
                    chat_id,
                    user_id,
                    until_date=until_date,
                    can_send_messages=False
                )
                warn = bot.send_message(
                    chat_id,
                    f"⚠️ User {message.from_user.first_name} ({user_id}) 12 ঘন্টার জন্য ব্যান করা হলো লিঙ্ক স্প্যাম করার কারণে!"
                )
                schedule_delete(chat_id, warn.message_id, delay=600)

        except Exception as e:
            print("Error:", e)
    else:
        # অন্য সব মেসেজ ৫ মিনিট পরে ডিলিট
        schedule_delete(chat_id, message.message_id, delay=300)

# ======================
# 🔹 Bot চালু
# ======================
print("🤖 Bot is running...")
bot.infinity_polling()