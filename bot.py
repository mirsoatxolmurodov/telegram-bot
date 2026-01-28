import telebot
from telebot import types
import sqlite3
import csv
import time


# ================== SOZLAMALAR ==================
TOKEN = "8205914721:AAG9pQGeX4_EGaoUuJXlma7IiUTxDsK6izM"
ADMIN_ID = 5390578467          # admin user_id
CHANNEL_USERNAME = "@mirsoat_club"
YOUTUBE_LINK = "https://youtube.com/"
ADMIN_USERNAME = "https://t.me/mirsoat_xolmurodov"


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
        types.InlineKeyboardButton("👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME[1:]}")
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


    # Kanalga majburiy a’zolik
    if uid != ADMIN_ID and not is_subscribed(uid):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Kanalga a’zo bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        bot.send_message(uid, "❗ Botdan foydalanish uchun kanalga a’zo bo‘ling.", reply_markup=kb)
        return


    sql.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = sql.fetchone()


    first = message.from_user.first_name
    last = message.from_user.last_name
    username = message.from_user.username


    # Yangi foydalanuvchi
    if not user:
        sql.execute(
            "INSERT INTO users (user_id, ref_id, referrals, active, first_name, last_name, username) "
            "VALUES (?, ?, 0, 1, ?, ?, ?)",
            (uid, ref_id, first, last, username)
        )


        if ref_id:
            # faqat referalni +1 qilamiz
            sql.execute(
                "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
                (ref_id,)
            )


            # Referal egasiga xabar
            try:
                bot.send_message(
                    ref_id,
                    f"🎉 Siz yangi foydalanuvchi qo‘shdingiz!\n"
                    f"👤 {first} {last if last else ''}"
                )
            except:
                pass


            # Admin xabari
            try:
                bot.send_message(
                    ADMIN_ID,
                    f"➕ Yangi referal qo‘shildi\n"
                    f"👤 {first} {last if last else ''}\n"
                    f"🔗 Kimdan: {ref_id}"
                )
            except:
                pass


        db.commit()


    # Admin panel
    if uid == ADMIN_ID:
        bot.send_message(uid, "👑 Admin panel", reply_markup=admin_keyboard())
    else:
        bot.send_message(uid, "✅ Xush kelibsiz!", reply_markup=main_keyboard())


# ================== CALLBACK ==================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    uid = call.from_user.id


    # ===== FOYDALANUVCHI =====
    if call.data == "ref" and uid != ADMIN_ID:
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        sql.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
        row = sql.fetchone()
        count = row[0] if row else 0


        bot.answer_callback_query(call.id)
        bot.send_message(
            uid,
            f"🔗 Sizning referal havolangiz:\n{link}\n\n👥 Taklif qilganlar: <b>{count}</b> ta"
        )
        return


    # ===== ADMIN =====
    if uid != ADMIN_ID:
        return


    if call.data == "stats":
        sql.execute("SELECT COUNT(*) FROM users")
        total = sql.fetchone()[0]
        sql.execute("SELECT COUNT(*) FROM users WHERE referrals>0")
        refs = sql.fetchone()[0]
        bot.answer_callback_query(call.id)
        bot.send_message(
            uid,
            f"📊 Statistika\n"
            f"👥 Jami foydalanuvchilar: {total}\n"
            f"🔗 Referal qilganlar: {refs}"
        )


    elif call.data == "top":
        sql.execute("""
        SELECT first_name, last_name, username, referrals
        FROM users
        WHERE active=1
        ORDER BY referrals DESC
        LIMIT 10
        """)
        rows = sql.fetchall()
        text = "🏆 <b>TOP 10 REFERALLAR</b>\n\n"
        for i, r in enumerate(rows, 1):
            uname = f"@{r[2]}" if r[2] else "yo‘q"
            text += f"{i}. {r[0]} {r[1] if r[1] else ''} ({uname}) — {r[3]} ta\n"
        bot.answer_callback_query(call.id)
        bot.send_message(uid, text)


    elif call.data == "export":
        sql.execute("SELECT * FROM users")
        rows = sql.fetchall()
        with open("users.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["user_id", "ref_id", "referrals", "active", "first_name", "last_name", "username"]
            )
            writer.writerows(rows)
        bot.answer_callback_query(call.id)
        bot.send_document(uid, open("users.csv", "rb"))


    elif call.data == "check":
        check_left_users()
        bot.answer_callback_query(call.id, "Tekshiruv tugadi")


# ================== TEKSHIRUV ==================
def check_left_users():
    sql.execute("SELECT user_id, ref_id FROM users WHERE active=1")
    users = sql.fetchall()


    for uid, ref in users:
        if not is_subscribed(uid):
            # faqat O‘SHA referal hisobdan 1 ta ayiriladi
            if ref:
                sql.execute(
                    "UPDATE users SET referrals = referrals - 1 WHERE user_id=? AND referrals>0",
                    (ref,)
                )
                try:
                    bot.send_message(
                        ref,
                        f"⚠️ Siz taklif qilgan foydalanuvchi ({uid}) kanalni tark etdi.\n"
                        f"➖ 1 referal olib tashlandi."
                    )
                except:
                    pass


            sql.execute("UPDATE users SET active=0 WHERE user_id=?", (uid,))
            try:
                bot.send_message(
                    uid,
                    "❗ Siz kanalni tark etdingiz. Referalingiz bekor qilindi."
                )
            except:
                pass


    db.commit()


# ================== START BOT ==================
print("Bot ishga tushdi...")
bot.infinity_polling()
