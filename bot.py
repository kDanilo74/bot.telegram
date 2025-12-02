import telebot
from telebot import types
import csv
import json
import os

# ========================
# 🔐 التوكن
# ========================
BOT_TOKEN = "8525745636:AAFOZoXtHl-1MxXkiBpm0AxiFEPBd4FcKsk"
SUPPORT_USER = "@karemdanilo"   # حط يوزر الدعم هنا

bot = telebot.TeleBot(BOT_TOKEN)

# ========================
# 📁 تحميل الحسابات
# ========================
ACCOUNTS_FILE = "users.csv"

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    with open(ACCOUNTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

accounts = load_accounts()

# ========================
# 📁 تحميل رصيد المستخدمين
# ========================
BALANCE_FILE = "balance.json"

def load_balance():
    if not os.path.exists(BALANCE_FILE):
        return {}
    with open(BALANCE_FILE, "r") as f:
        return json.load(f)

def save_balance(bal):
    with open(BALANCE_FILE, "w") as f:
        json.dump(bal, f)

balances = load_balance()

# ========================
# 📌 لوحة الأزرار
# ========================
def main_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add("📝 Do Task", "💰 My Balance")
    menu.add("🔗 Referral Link", "🆘 Support")
    return menu

# ========================
# 🚀 Start
# ========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    if user_id not in balances:
        balances[user_id] = 0
        save_balance(balances)

    # رابط الإحالة
    referral = f"https://t.me/{bot.get_me().username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        f"🔰 **Welcome!**\n\n"
        f"🌍 اللغة يتم تحديدها تلقائيًا حسب جهازك.\n"
        f"💸 نفّذ المهام واحصل على أرباح.\n\n"
        f"🔗 رابط الإحالة الخاص بك:\n{referral}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ========================
# 📝 تنفيذ مهمة
# ========================
@bot.message_handler(func=lambda m: m.text == "📝 Do Task")
def do_task(message):
    if not accounts:
        bot.send_message(message.chat.id, "❌ لا توجد مهام متاحة الآن.")
        return

    acc = accounts.pop(0)

    text = (
        "🎯 **Your Task**\n\n"
        f"👤 First Name: `{acc['first']}`\n"
        f"👥 Last Name: `{acc['last']}`\n"
        f"📧 Email: `{acc['email']}`\n"
        f"🔐 Password: `{acc['password']}`\n\n"
        "بعد تنفيذ المهمة — ابعت إثباتك."
    )

    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ========================
# 💰 الرصيد
# ========================
@bot.message_handler(func=lambda m: m.text == "💰 My Balance")
def balance(message):
    user_id = str(message.chat.id)
    bal = balances.get(user_id, 0)
    bot.send_message(message.chat.id, f"💰 Your Balance: **{bal}$**", parse_mode="Markdown")

# ========================
# 🔗 الإحالة
# ========================
@bot.message_handler(func=lambda m: m.text == "🔗 Referral Link")
def referral(message):
    user_id = str(message.chat.id)
    referral = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(
        message.chat.id,
        f"🔗 Your referral link:\n{referral}\n\n"
        "🎁 تحصل على 0.02$ عند أول مهمة من إحالتك!",
        parse_mode="Markdown"
    )

# ========================
# 🆘 الدعم الفني
# ========================
@bot.message_handler(func=lambda m: m.text == "🆘 Support")
def support(message):
    bot.send_message(
        message.chat.id,
        f"🆘 **للتواصل مع الدعم:**\n{SUPPORT_USER}",
        parse_mode="Markdown"
    )

# ========================
# 🟢 إشعار بعد إرسال المال
# ========================
def notify_payment(user_id, amount):
    try:
        bot.send_message(
            user_id,
            f"✅ تم إرسال **{amount}$** إلى محفظتك.\nشكراً لاستخدامك خدمتنا!"
        )
    except:
        pass

# ========================
# تشغيل البوت
# ========================
print("BOT RUNNING...")
bot.polling(none_stop=True)
