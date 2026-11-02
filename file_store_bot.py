import os
import telebot
from flask import Flask
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Render ke environment variables se token uthayega
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("⚠️ WARNING: BOT_TOKEN nahi mila! Render me Environment Variable set karein.")
    
bot = telebot.TeleBot(BOT_TOKEN)

# File save karne ka folder (Render par ye /tmp me banega)
if not os.path.exists("files"):
    os.makedirs("files")

# --- RENDER KE LIYE WEB SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "File Store Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📤 Upload File", callback_data="upload"),
        InlineKeyboardButton("📥 Get File", callback_data="get")
    )
    bot.reply_to(message, "👋 Welcome to File Store Bot!\n\nMujhe koi bhi file/document bhejo, main use save kar lunga.", reply_markup=markup)

@bot.message_handler(content_types=['document', 'photo', 'video', 'audio'])
def handle_file(message):
    try:
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
        elif message.photo:
            file_id = message.photo[-1].file_id
            file_name = f"photo_{file_id[:5]}.jpg"
        elif message.video:
            file_id = message.video.file_id
            file_name = f"video_{file_id[:5]}.mp4"
        elif message.audio:
            file_id = message.audio.file_id
            file_name = message.audio.title or f"audio_{file_id[:5]}.mp3"

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        save_path = os.path.join("files", file_name)
        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, f"✅ File Successfully Saved!\nName: {file_name}\n\nAb isko download karne ke liye file ka naam likho.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data == "get")
def ask_file_name(call):
    bot.send_message(call.message.chat.id, "📝 File ka naam likho jo download karna hai:")

@bot.callback_query_handler(func=lambda call: call.data == "upload")
def ask_upload(call):
    bot.send_message(call.message.chat.id, "📤 Mujhe koi bhi file/document bhejo.")

@bot.message_handler(func=lambda message: True)
def send_file(message):
    file_name = message.text.strip()
    save_path = os.path.join("files", file_name)

    if os.path.exists(save_path):
        with open(save_path, 'rb') as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.reply_to(message, "❌ Ye file nahi mili. Check karo naam sahi hai?")

# Flask server ko background me start karo
threading.Thread(target=run_flask).start()

# Bot start karo
print("File Store Bot is running...")
bot.remove_webhook()
bot.infinity_polling()
