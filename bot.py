import os
import telebot
from telebot import types
import sqlite3
import csv


# ================== SOZLAMALAR ==================
TOKEN = os.getenv("8205914721:AAFkrlLErg2JOxG4z_iFVSipNuMQrcxZ0oU")
ADMIN_ID = int(os.getenv("5390578467"))
CHANNEL_USERNAME = os.getenv("mirsoat_club")
YOUTUBE_LINK = os.getenv("YOUTUBE_LINK")
ADMIN_USERNAME = os.getenv("mirsoat_xolmurodov")


bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


# ================== DATABASE ==================
db = sqlite3.connect("users.db", check_same_thread=False)
sql = db.cursor()


sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    ref_id INTEGER,
    referrals INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1,
    first_name TEXT,
    last_name TEXT,
    username TEXT
)
""")
db.commit()


# ================== YORDAMCHI ==================
def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ("member", "administrator", "creator")
    except:
        return False


def main_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔗 Referal ssilka", callback_data="ref"),
        types.InlineKeyboardButton("📺 YouTube", url=YOUTUBE_LINK),
        types.InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    return kb


def admin_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🔍 Tekshiruv", callback_data="check"),
        types.InlineKeyboardButton("📊 Statistika", callback_data="stats"),
        types.InlineKeyboardButton("🏆 TOP referallar", callback_data="top"),
        types.InlineKeyboardButton("📁 CSV yuklash", callback_data="export")
    )
    return kb


# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    args = message.text.split()
    ref_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None


    if uid != ADMIN_ID and not is_subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "✅ Kanalga a’zo bo‘lish",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
        ))
        bot.send_message(uid, "❗ Kanalga a’zo bo‘ling.", reply_markup=kb)
        return


    sql.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = sql.fetchone()


    first = message.from_user.first_name
    last = message.from_user.last_name
    username = message.from_user.username


    if not user:
        sql.execute("""
        INSERT INTO users (user_id, ref_id, first_name, last_name, username)
        VALUES (?, ?, ?, ?, ?)
        """, (uid, ref_id, first, last, username))


        if ref_id:
            sql.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (ref_id,))
            try:
                bot.send_message(ref_id, f"🎉 Yangi referal: {first}")
            except:
                pass


        db.commit()


    if uid == ADMIN_ID:
        bot.send_message(uid, "👑 Admin panel", reply_markup=admin_keyboard())
    else:
        bot.send_message(uid, "✅ Xush kelibsiz!", reply_markup=main_keyboard())


# ================== CALLBACK ==================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    uid = call.from_user.id


    if call.data == "ref":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        sql.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
        count = sql.fetchone()[0]
        bot.send_message(uid, f"🔗 Havola:\n{link}\n\n👥 {count} ta")
        return


    if uid != ADMIN_ID:
        return


    if call.data == "stats":
        sql.execute("SELECT COUNT(*) FROM users")
        total = sql.fetchone()[0]
        bot.send_message(uid, f"👥 Jami: {total}")


    elif call.data == "export":
        sql.execute("SELECT * FROM users")
        rows = sql.fetchall()
        with open("users.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id","ref_id","referrals","active","first","last","username"])
            writer.writerows(rows)
        bot.send_document(uid, open("users.csv", "rb"))


# ================== RUN ==================
print("Bot ishga tushdi...")
bot.infinity_polling()

