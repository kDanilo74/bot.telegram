# bot.py
# نسخة مُنفّذة للمطلوب: أزرار تعمل، نظام إحالات، توليد إيميلات من قائمة أسماء، حفظ في CSV.
# ملاحظة أمان: التوكن مكشوف هنا لأنك طلبت استخدام التوكن القديم. غيّره بعد التجربة إن أمكن.

import os
import csv
import random
import string
import telebot
from pathlib import Path
from urllib.parse import quote_plus

# =========================
# إعدادات (مضمنة بالتحديد اللي طلبته)
# =========================
TOKEN = "8525745636:AAFOZoXtHl-1MxXkiBpm0AxiFEPBd4FcKsk"   # توكنك (موجود هنا كما طلبت)
ADMIN_ID = 7152023720

bot = telebot.TeleBot(TOKEN)

# =========================
# ملفات البيانات
# =========================
DATA_FILE = Path("users_data.csv")      # user_id,balance
ACCOUNTS_FILE = Path("users.csv")       # first,last,email,password (accounts used as "مهام")
REF_FILE = Path("referrals.csv")        # user_id,referer,is_first_task_done
PENDING_FILE = Path("pending_tasks.csv")# chat_id,task_text

NAMES_SOURCE = Path("names.txt")        # ضع هنا قائمة الأسماء (التي أرسلتها) - كل سطر: "First Last"

# حافظ على حالة انتظار المهمة
user_pending_task = {}  # chat_id -> True/False

# =========================
# تهيئة ملفات CSV إذا غير موجودة
# =========================
def ensure_files():
    if not DATA_FILE.exists():
        with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "balance"])

    if not REF_FILE.exists():
        with REF_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "referer", "is_first_task_done"])

    # accounts file header
    if not ACCOUNTS_FILE.exists():
        with ACCOUNTS_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["first", "last", "email", "password"])

    if not PENDING_FILE.exists():
        with PENDING_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["chat_id", "task_text"])

ensure_files()

# =========================
# دوال مساعدة للتعامل مع CSV
# =========================
def read_csv_as_list(path):
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    return rows

def append_csv_row(path, row):
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def write_csv_rows(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

# =========================
# رصيد المستخدم
# =========================
def get_balance(user_id):
    rows = read_csv_as_list(DATA_FILE)
    # rows[0] is header
    for row in rows[1:]:
        if row and row[0] == str(user_id):
            try:
                return float(row[1])
            except:
                return 0.0
    return 0.0

def update_balance(user_id, amount):
    rows = read_csv_as_list(DATA_FILE)
    header = rows[0] if rows else ["user_id", "balance"]
    body = rows[1:] if len(rows) > 1 else []
    found = False
    for r in body:
        if r and r[0] == str(user_id):
            try:
                r[1] = str(float(r[1]) + float(amount))
            except:
                r[1] = str(float(amount))
            found = True
            break
    if not found:
        body.append([str(user_id), str(float(amount))])
    write_csv_rows(DATA_FILE, header, body)

# =========================
# قراءة/توليد الحسابات من names.txt (مرة واحدة عند الفراغ)
# =========================
def email_normalize(s):
    return "".join(ch for ch in s.lower() if ch.isalnum() or ch == ".")

def generate_email(first, last, existing_emails):
    base = f"{email_normalize(first)}.{email_normalize(last)}"
    # جرب توليد بدون أرقام ثم بأرقام لضمان عدم التكرار داخل ملفنا
    candidate = f"{base}@gmail.com"
    if candidate not in existing_emails:
        return candidate
    # أضف رقم عشوائي
    for _ in range(1000):
        num = random.randint(10, 9999)
        candidate = f"{base}{num}@gmail.com"
        if candidate not in existing_emails:
            return candidate
    # كحل افتراضي لو حصل تكرار نادر
    suffix = "".join(random.choices(string.ascii_lowercase+string.digits, k=4))
    return f"{base}{suffix}@gmail.com"

def load_names_and_create_accounts():
    # إذا users.csv فيه حسابات فلا نفعل
    rows = read_csv_as_list(ACCOUNTS_FILE)
    if len(rows) > 1:
        return  # فيه حسابات مسبقا، لا نعيد توليد
    # اقرأ قائمة الأسماء من names.txt
    if not NAMES_SOURCE.exists():
        print(f"[INFO] file {NAMES_SOURCE} not found. ضع قائمة الأسماء في ملف names.txt كل سطر: First Last")
        return

    # اقرأ الاسماء
    lines = [ln.strip() for ln in NAMES_SOURCE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    existing_emails = set()
    accounts = []
    for ln in lines:
        parts = ln.split()
        if len(parts) >= 2:
            first = parts[0].strip()
            last = " ".join(parts[1:]).strip()
        elif len(parts) == 1:
            first = parts[0].strip()
            last = "x"
        else:
            continue
        email = generate_email(first, last, existing_emails)
        existing_emails.add(email)
        # كلمة مرور عشوائية بسيطة (يمكن تخصيصها)
        password = "".join(random.choices(string.ascii_letters+string.digits, k=8))
        accounts.append([first, last, email, password])

    # اكتب accounts إلى users.csv
    header = ["first", "last", "email", "password"]
    write_csv_rows(ACCOUNTS_FILE, header, accounts)
    print(f"[INFO] Generated {len(accounts)} accounts into {ACCOUNTS_FILE}")

# اندار: حاول توليد الحسابات مرة واحدة عند التشغيل لو الملف فاضي
load_names_and_create_accounts()

# =========================
# نظام الإحالات
# =========================
def register_referral(user, ref):
    if not ref:
        return
    if str(user) == str(ref):
        return
    rows = read_csv_as_list(REF_FILE)
    header = rows[0] if rows else ["user_id", "referer", "is_first_task_done"]
    body = rows[1:] if len(rows) > 1 else []
    # لو المستخدم مسجل مسبقًا — لا نعطي إحالة جديدة
    for r in body:
        if r and r[0] == str(user):
            return
    body.append([str(user), str(ref), "0"])
    write_csv_rows(REF_FILE, header, body)

def referral_first_task_reward(user_id):
    rows = read_csv_as_list(REF_FILE)
    header = rows[0] if rows else ["user_id", "referer", "is_first_task_done"]
    body = rows[1:] if len(rows) > 1 else []
    changed = False
    referrer = None
    for r in body:
        if r and r[0] == str(user_id) and r[2] == "0":
            referrer = r[1]
            r[2] = "1"
            changed = True
            break
    if changed:
        write_csv_rows(REF_FILE, header, body)
    if referrer:
        try:
            update_balance(referrer, 0.02)
        except Exception as e:
            print("Error giving referral reward:", e)

# =========================
# جلب مهمة (حساب) عشوائي
# =========================
def get_account():
    rows = read_csv_as_list(ACCOUNTS_FILE)
    body = rows[1:] if len(rows) > 1 else []
    if not body:
        return None
    return random.choice(body)

# =========================
# القائمة الرئيسية
# =========================
def main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📝 المهام", "💰 رصيدي")
    markup.row("🔗 رابط الإحالة", "💵 سحب الأرباح")
    markup.row("📍 حسابي")
    bot.send_message(chat_id, "اختر من القائمة:", reply_markup=markup)

# =========================
# START handler: يدعم ref param
# =========================
@bot.message_handler(commands=['start'])
def start_message(message):
    parts = message.text.split()
    if len(parts) > 1:
        ref = parts[1]
        # ref عادة تكون id أو token -- نحفظها كما وردت
        try:
            register_referral(message.from_user.id, ref)
        except Exception:
            pass

    main_menu(message.chat.id)

# =========================
# زر: المهام
# =========================
@bot.message_handler(func=lambda m: m.text == "📝 المهام")
def send_task(message):
    account = get_account()
    if account is None:
        bot.send_message(message.chat.id, "❗ لا توجد حسابات متاحة حالياً. تواصل مع الإدارة.")
        return

    first, last, email, password = account
    task_text = (
        f"🔹 بيانات المهمة:\n\n"
        f"الاسم: {first} {last}\n"
        f"الإيميل: {email}\n"
        f"كلمة المرور: {password}\n\n"
        f"⚠ بعد التنفيذ أرسل رسالة نصية تؤكد إتمام المهمة."
    )

    user_pending_task[message.chat.id] = True
    # سجّل المهمة قيد المراجعة مؤقتاً
    append_csv_row(PENDING_FILE, [str(message.chat.id), task_text])
    bot.send_message(message.chat.id, task_text)

# =========================
# زر: رابط الإحالة
# =========================
@bot.message_handler(func=lambda m: m.text == "🔗 رابط الإحالة")
def send_ref_link(message):
    # نُنشئ رابط إحالة بسيط: bot_username?start=ref{user_id}
    bot_username = bot.get_me().username or "your_bot"
    ref_token = f"ref{message.from_user.id}"
    referral_link = f"https://t.me/{bot_username}?start={quote_plus(ref_token)}"
    note = "ملاحظة: عند أول مهمة يقوم بها الشخص الذي يدخُل من خلال الرابط، سيحصل صاحب الرابط على 0.02 USDT كمكافأة (مرة واحدة فقط)."
    bot.send_message(message.chat.id, f"🔗 رابط الإحالة الخاص بك:\n{referral_link}\n\n{note}")

# =========================
# زر: رصيدي
# =========================
@bot.message_handler(func=lambda m: m.text == "💰 رصيدي")
def balance_handler(message):
    balance = get_balance(message.chat.id)
    bot.send_message(message.chat.id, f"💰 رصيدك الحالي: {balance:.8f} USDT")

# =========================
# زر: حسابي
# =========================
@bot.message_handler(func=lambda m: m.text == "📍 حسابي")
def account_handler(message):
    balance = get_balance(message.chat.id)
    bot.send_message(message.chat.id, f"🆔 ID: {message.chat.id}\n💰 الرصيد: {balance:.8f} USDT")

# =========================
# زر: سحب الأرباح
# =========================
@bot.message_handler(func=lambda m: m.text == "💵 سحب الأرباح")
def withdraw_handler(message):
    balance = get_balance(message.chat.id)
    if balance < 1:
        bot.send_message(message.chat.id, "❗ الحد الأدنى للسحب هو 1 USDT")
    else:
        bot.send_message(message.chat.id, "💵 أرسل عنوان محفظة USDT TRC20:")
        bot.register_next_step_handler(message, get_wallet)

def get_wallet(message):
    wallet = message.text.strip()
    # أرسل طلب السحب للإدمن
    bot.send_message(ADMIN_ID, f"🔔 طلب سحب جديد\nمن: {message.chat.id}\nالمحفظة: {wallet}\nالرصيد: {get_balance(message.chat.id):.8f} USDT")
    bot.send_message(message.chat.id, "⏳ تم إرسال طلبك للإدارة")

# =========================
# رفض الملفات/صور أثناء انتظار إثبات المهمة
# =========================
@bot.message_handler(content_types=['photo','video','document','sticker','animation'])
def reject_proof(message):
    if user_pending_task.get(message.chat.id):
        bot.send_message(message.chat.id, "⚠ يجب إرسال رسالة نصية فقط لتأكيد المهمة.")
    else:
        bot.send_message(message.chat.id, "❗ لا توجد مهمة تنتظر التنفيذ.")

# =========================
# استلام إثبات المهمة — هذا الهاندلر يعمل فقط إذا المستخدم فعلاً في انتظار
# =========================
@bot.message_handler(func=lambda m: user_pending_task.get(m.chat.id) == True)
def receive_proof(message):
    # أرسل الأدمن رسالة مع أزرار قبول/رفض
    try:
        bot.send_message(ADMIN_ID, f"📩 إثبات مهمة جديدة\nمن المستخدم: {message.chat.id}\n\nالرسالة:\n{message.text}")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("✔ قبول", callback_data=f"accept_{message.chat.id}"),
            telebot.types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{message.chat.id}")
        )
        bot.send_message(ADMIN_ID, "اختار:", reply_markup=markup)
        bot.send_message(message.chat.id, "⏳ تم إرسال مهمتك للمراجعة.")
        user_pending_task[message.chat.id] = False
    except Exception as e:
        bot.send_message(message.chat.id, "❗ حدث خطأ أثناء إرسال الإثبات للإدارة.")
        print("Error sending proof to admin:", e)

# =========================
# قبول / رفض من الأدمن
# =========================
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(callback):
    if callback.from_user.id != ADMIN_ID:
        return
    data = callback.data or ""
    if data.startswith("accept_"):
        uid_str = data.split("_",1)[1]
        try:
            uid = int(uid_str)
        except:
            uid = uid_str
        update_balance(uid, 0.05)
        # منحة الإحالة لأول مهمة
        referral_first_task_reward(uid)
        bot.send_message(uid, "✔ تم قبول المهمة!\n+0.05 USDT")
        bot.send_message(ADMIN_ID, "✔ تم القبول.")
    elif data.startswith("reject_"):
        uid_str = data.split("_",1)[1]
        try:
            uid = int(uid_str)
        except:
            uid = uid_str
        bot.send_message(uid, "❌ تم رفض المهمة.")
        bot.send_message(ADMIN_ID, "❌ تم الرفض.")

# =========================
# تشغيل البوت
# =========================
if __name__ == "__main__":
    print("Bot is running...")
    try:
        bot.infinity_polling(timeout=60)
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Stopped with error:", e)
