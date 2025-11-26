import os
import logging
import sqlite3
import random
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# تكوين البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8500469877:AAGCNojz50p2U2RJrQ85TEGuuR4b-S7XaLo')

# إعداد السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# كود Keep-Alive
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is Running!"

@app.route('/health')
def health():
    return "✅ Bot is Healthy"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# بدء الخادم
Thread(target=run_flask, daemon=True).start()

class BotDatabase:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        
        # الجداول الأساسية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_string TEXT UNIQUE,
                phone TEXT,
                name TEXT,
                username TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                is_super_admin BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")

class BotHandler:
    def __init__(self):
        self.db = BotDatabase()
        self.application = None
        self.setup_handlers()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎮 **لوحة تحكم البوت المتكامل**\n\n"
            "اختر القسم الذي تريد إدارته:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "manage_accounts":
            await query.edit_message_text(
                "👥 **إدارة الحسابات**\n\n"
                "سيتم إضافة الميزات قريباً...",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                "🛠 **قيد التطوير**\n\n"
                "هذه الميزة قيد التطوير حالياً...",
                parse_mode='Markdown'
            )
    
    def setup_handlers(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # إضافة المشرف الافتراضي
        self.db.add_admin(8390377822, "@user", "المشرف الرئيسي", True)
    
    def run(self):
        print("🤖 Starting Telegram Bot...")
        self.application.run_polling()
        print("✅ Bot started successfully")

def main():
    print("🚀 Starting Telegram Bot Server...")
    print("✅ Keep-Alive server started")
    
    try:
        bot = BotHandler()
        bot.run()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        # ابقاء البرنامج يعمل حتى مع وجود خطأ
        import time
        while True:
            time.sleep(60)
            print("🟢 Server is still alive...")

if __name__ == "__main__":
    main()
