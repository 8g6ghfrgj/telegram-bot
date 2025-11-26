import os
import logging
import sqlite3
import threading
import time
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# تكوين البوت
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8500469877:AAGCNojz50p2U2RJrQ85TEGuuR4b-S7XaLo')

# إعداد السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("=" * 50)
print("🚀 STARTING TELEGRAM BOT SERVER")
print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
print("=" * 50)

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

# بدء خادم Flask في thread منفصل
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()
print("✅ Flask server started")

class BotDatabase:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                is_super_admin BOOLEAN DEFAULT 0
            )
        ''')
        
        # إضافة المشرف الرئيسي إذا لم يكن موجوداً
        cursor.execute('SELECT id FROM admins WHERE user_id = ?', (8390377822,))
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO admins (user_id, username, full_name, is_super_admin) VALUES (?, ?, ?, ?)',
                (8390377822, "@user", "المشرف الرئيسي", 1)
            )
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")

    def is_admin(self, user_id):
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM admins WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

class BotHandler:
    def __init__(self):
        self.db = BotDatabase()
        self.application = None
        self.setup_handlers()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id
        
        if not self.db.is_admin(user_id):
            await update.message.reply_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
            return
        
        keyboard = [
            [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
            [InlineKeyboardButton("💬 إدارة الردود", callback_data="manage_replies")],
            [InlineKeyboardButton("👨‍💼 إدارة المشرفين", callback_data="manage_admins")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎮 **لوحة تحكم البوت المتكامل**\n\n"
            "اختر القسم الذي تريد إدارته:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        print(f"✅ User {user_id} used /start command")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        if not self.db.is_admin(user_id):
            await query.edit_message_text("❌ ليس لديك صلاحية للوصول إلى هذا البوت.")
            return
        
        data = query.data
        
        if data == "manage_accounts":
            await query.edit_message_text("👥 **إدارة الحسابات**\n\nسيتم إضافة الميزات قريباً...", parse_mode='Markdown')
        elif data == "back_to_main":
            await self.start_from_query(query, context)
        else:
            await query.edit_message_text("🛠 **قيد التطوير**\n\nهذه الميزة قيد التطوير حالياً...", parse_mode='Markdown')
        
        print(f"✅ User {user_id} pressed button: {data}")
    
    async def start_from_query(self, query, context):
        keyboard = [
            [InlineKeyboardButton("👥 إدارة الحسابات", callback_data="manage_accounts")],
            [InlineKeyboardButton("📢 إدارة الإعلانات", callback_data="manage_ads")],
            [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="manage_groups")],
            [InlineKeyboardButton("💬 إدارة الردود", callback_data="manage_replies")],
            [InlineKeyboardButton("👨‍💼 إدارة المشرفين", callback_data="manage_admins")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎮 **لوحة تحكم البوت المتكامل**\n\nاختر القسم الذي تريد إدارته:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    def setup_handlers(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        print("✅ Telegram bot handlers setup completed")
    
    def run(self):
        print("🤖 Starting Telegram Bot polling...")
        self.application.run_polling(drop_pending_updates=True)
        print("❌ Telegram Bot stopped (this shouldn't happen)")

def start_bot():
    """تشغيل البوت في thread منفصل"""
    try:
        bot = BotHandler()
        bot.run()
    except Exception as e:
        print(f"❌ Error in bot thread: {e}")
        # إعادة المحاولة بعد 10 ثواني
        time.sleep(10)
        start_bot()

def main():
    print("🚀 Starting main server process...")
    
    # بدء البوت في thread منفصل
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    print("✅ Telegram Bot thread started")
    
    # ابقاء البرنامج الرئيسي يعمل
    counter = 0
    while True:
        print(f"🟢 Main server running... ({counter}) - Bot should be receiving messages")
        counter += 1
        time.sleep(30)

if __name__ == "__main__":
    main()
