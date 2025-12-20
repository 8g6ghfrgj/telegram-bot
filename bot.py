import os
import re
import time
import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
    CommandHandler,
    CallbackQueryHandler
)

# ===============================
# الإعدادات
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 7

# ===============================
# أدوات
# ===============================
def clean_link(link: str) -> str:
    return (
        link.replace("*", "")
        .replace("(", "")
        .replace(")", "")
        .replace("[", "")
        .replace("]", "")
        .strip()
    )


def extract_links(line: str):
    return re.findall(r'https?://t\.me/[^\s]+', line)


def is_bot(link: str) -> bool:
    return link.rstrip("/").split("/")[-1].lower().endswith("bot")


def classify_public_link(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        html = r.text.lower()
        if "members" in html:
            return "group"
        if "subscribers" in html:
            return "channel"
    except:
        pass
    return "channel"


def is_alive(url: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code == 200
    except:
        return False


# ===============================
# /start
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 بوت تصفية روابط تيليجرام\n\n"
        "📄 أرسل ملف TXT\n"
        "سيتم تقسيمه إلى:\n"
        "• قنوات\n"
        "• مجموعات\n"
        "• بوتات\n"
        "• روابط رسائل\n\n"
        "بعدها يمكنك تصفية الروابط الميتة بزر واحد."
    )


# ===============================
# معالجة الملف الأساسي
# ===============================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith(".txt"):
        await update.message.reply_text("❌ أرسل ملف TXT فقط")
        return

    file = await doc.get_file()
    lines = (await file.download_as_bytearray()).decode("utf-8", errors="ignore").splitlines()

    status = await update.message.reply_text("📥 تم استلام الملف – جاري التصفية...")

    files = {
        "channels": ("channels.txt", set()),
        "groups": ("groups.txt", set()),
        "bots": ("bots.txt", set()),
        "messages": ("messages.txt", set())
    }

    opened = {k: open(v[0], "w", encoding="utf-8") for k, v in files.items()}

    for line in lines:
        line = clean_link(line)
        if "t.me/" not in line:
            continue

        for link in extract_links(line):

            if "/c/" in link:
                gid = re.search(r'/c/(\d+)', link)
                if gid and gid.group(1) not in files["messages"][1]:
                    opened["messages"].write(link + "\n")
                    files["messages"][1].add(gid.group(1))
                continue

            if is_bot(link):
                if link not in files["bots"][1]:
                    opened["bots"].write(link + "\n")
                    files["bots"][1].add(link)
                continue

            kind = classify_public_link(link)
            if link not in files[kind + "s"][1]:
                opened[kind + "s"].write(link + "\n")
                files[kind + "s"][1].add(link)

    for f in opened.values():
        f.close()

    await status.edit_text("✅ انتهت التصفية – جاري إرسال الملفات")

    for key, (fname, _) in files.items():
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🧹 تصفية الروابط الميتة", callback_data=f"clean::{fname}")]
        ])
        await update.message.reply_document(
            open(fname, "rb"),
            caption=f"📄 {key}",
            reply_markup=keyboard
        )

        context.bot_data[fname] = fname

        os.remove(fname)


# ===============================
# زر تصفية الروابط الميتة
# ===============================
async def clean_dead_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    fname = query.data.split("::")[1]

    if fname not in context.bot_data:
        await query.edit_message_caption("❌ الملف غير متوفر")
        return

    await query.edit_message_caption("⏳ جاري فحص الروابط النشطة...")

    alive_file = f"alive_{fname}"

    with open(fname, "r", encoding="utf-8") as fin, \
         open(alive_file, "w", encoding="utf-8") as fout:
        for line in fin:
            link = line.strip()
            if is_alive(link):
                fout.write(link + "\n")

    await query.message.reply_document(
        open(alive_file, "rb"),
        caption="✅ الروابط النشطة فقط"
    )

    os.remove(alive_file)


# ===============================
# تشغيل
# ===============================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(clean_dead_links, pattern=r"^clean::"))

    print("🤖 Bot running with clean buttons...")
    app.run_polling()


if __name__ == "__main__":
    main()
