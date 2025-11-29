# bot_i18n.py
# Modified version of the user's bot.py to support multilingual UI (ar,en,fr,ru)
# NOTE: Keep your TOKEN private. This file preserves the token from the original file as requested.
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
# نظام اللغات (i18n)
# =========================
LANG = {
    "ar": {
        "menu": "اختر من القائمة:",
        "tasks": "📝 المهام",
        "balance": "💰 رصيدي",
        "ref": "🔗 رابط الإحالة",
        "withdraw": "💵 سحب الأرباح",
        "account": "📍 حسابي",

        "no_accounts": "❗ لا توجد حسابات متاحة حالياً.",
        "task_details": "🔹 بيانات المهمة:\n\nالاسم: {first} {last}\nالإيميل: {email}\nكلمة المرور: {password}\n\n⚠ بعد التنفيذ أرسل رسالة نصية تؤكد إتمام المهمة.",
        "proof_received": "⏳ تم إرسال مهمتك للمراجعة.",
        "send_text_only": "⚠ يجب إرسال رسالة نصية فقط لتأكيد المهمة.",
        "no_pending": "❗ لا توجد مهمة تنتظر التنفيذ.",

        "balance_msg": "💰 رصيدك الحالي: {bal} USDT",
        "account_info": "🆔 ID: {id}\n💰 الرصيد: {bal} USDT",

        "withdraw_address": "💵 أرسل عنوان محفظة USDT TRC20:",
        "withdraw_min": "❗ الحد الأدنى للسحب هو 1 USDT",
        "withdraw_sent": "⏳ تم إرسال طلبك للإدارة",

        "ref_link_note": "ملاحظة: عند أول مهمة يقوم بها الشخص الذي يدخُل من خلال الرابط، سيحصل صاحب الرابط على 0.02 USDT كمكافأة (مرة واحدة فقط)."
    },

    "en": {
        "menu": "Choose from the menu:",
        "tasks": "📝 Tasks",
        "balance": "💰 My Balance",
        "ref": "🔗 Referral Link",
        "withdraw": "💵 Withdraw",
        "account": "📍 My Account",

        "no_accounts": "❗ No accounts available right now.",
        "task_details": "🔹 Task Details:\n\nName: {first} {last}\nEmail: {email}\nPassword: {password}\n\n⚠ After completing the task, send a text message to confirm.",
        "proof_received": "⏳ Your task was sent for review.",
        "send_text_only": "⚠ You must send *text only* to confirm the task.",
        "no_pending": "❗ No pending task.",

        "balance_msg": "💰 Your balance: {bal} USDT",
        "account_info": "🆔 ID: {id}\n💰 Balance: {bal} USDT",

        "withdraw_address": "💵 Send your USDT TRC20 wallet address:",
        "withdraw_min": "❗ Minimum withdrawal is 1 USDT",
        "withdraw_sent": "⏳ Your withdrawal request was submitted",

        "ref_link_note": "Note: When the first task is completed by someone who joins through your link, you'll receive 0.02 USDT (one-time)."
    },

    "fr": {
        "menu": "Choisissez dans le menu :",
        "tasks": "📝 Tâches",
        "balance": "💰 Mon Solde",
        "ref": "🔗 Lien de Parrainage",
        "withdraw": "💵 Retrait",
        "account": "📍 Mon Compte",

        "no_accounts": "❗ Aucun compte disponible pour le moment.",
        "task_details": "🔹 Détails de la tâche :\n\nNom : {first} {last}\nEmail : {email}\nMot de passe : {password}\n\n⚠ Après avoir terminé, envoyez un message texte pour confirmer.",
        "proof_received": "⏳ Votre tâche a été envoyée pour vérification.",
        "send_text_only": "⚠ Vous devez envoyer uniquement un message texte pour confirmer la tâche.",
        "no_pending": "❗ Aucune tâche en attente.",

        "balance_msg": "💰 Votre solde : {bal} USDT",
        "account_info": "🆔 ID : {id}\n💰 Solde : {bal} USDT",

        "withdraw_address": "💵 Envoyez votre adresse USDT TRC20 :",
        "withdraw_min": "❗ Le retrait minimum est de 1 USDT",
        "withdraw_sent": "⏳ Votre demande de retrait a été envoyée",

        "ref_link_note": "Remarque : Lorsque la première tâche est terminée par une personne qui rejoint via votre lien, vous recevrez 0.02 USDT (une seule fois)."
    },

    "ru": {
        "menu": "Выберите из меню:",
        "tasks": "📝 Задания",
        "balance": "💰 Мой баланс",
        "ref": "🔗 Реферальная ссылка",
        "withdraw": "💵 Вывод средств",
        "account": "📍 Мой аккаунт",

        "no_accounts": "❗ Нет доступных аккаунтов.",
        "task_details": "🔹 Детали задания:\n\nИмя: {first} {last}\nEmail: {email}\nПароль: {password}\n\n⚠ После выполнения отправьте текстовое сообщение для подтверждения.",
        "proof_received": "⏳ Ваше задание отправлено на проверку.",
        "send_text_only": "⚠ Отправьте *только текст*, чтобы подтвердить выполнение.",
        "no_pending": "❗ Нет ожидающих заданий.",

        "balance_msg": "💰 Ваш баланс: {bal} USDT",
        "account_info": "🆔 ID: {id}\n💰 Баланс: {bal} USDT",

        "withdraw_address": "💵 Отправьте адрес кошелька USDT TRC20:",
        "withdraw_min": "❗ Минимальная сумма вывода — 1 USDT",
        "withdraw_sent": "⏳ Ваш запрос на вывод отправлен",

        "ref_link_note": "Примечание: Когда первый выполненный таск от пользователя, пришедшего по вашей ссылке, будет принят, вы получите 0.02 USDT (один раз)."
    }
}

# Helper to list all button labels for handlers to match user presses
ALL_TASK_LABELS = [LANG[k]["tasks"] for k in LANG]
ALL_BALANCE_LABELS = [LANG[k]["balance"] for k in LANG]
ALL_REF_LABELS = [LANG[k]["ref"] for k in LANG]
ALL_WITHDRAW_LABELS = [LANG[k]["withdraw"] for k in LANG]
ALL_ACCOUNT_LABELS = [LANG[k]["account"] for k in LANG]

def L(user, key, **kwargs):
    # user can be a telebot.types.User or a simple object with language_code attribute
    lang = getattr(user, "language_code", None)
    if not lang or lang not in LANG:
        lang = "en"
    text = LANG[lang].get(key, "")
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

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
# القائمة الرئيسية (now language-aware)
# =========================
def main_menu(chat_id, user):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(L(user, "tasks"), L(user, "balance"))
    markup.row(L(user, "ref"), L(user, "withdraw"))
    markup.row(L(user, "account"))
    bot.send_message(chat_id, L(user, "menu"), reply_markup=markup)

# =========================
# START handler: يدعم ref param ويريح اللغة فوراً
# =========================
@bot.message_handler(commands=['start'])
def start_message(message):
    parts = message.text.split()
    if len(parts) > 1:
        ref = parts[1]
        try:
            register_referral(message.from_user.id, ref)
        except Exception:
            pass

    # send localized welcome and menu
    bot.send_message(message.chat.id, L(message.from_user, "menu"))
    main_menu(message.chat.id, message.from_user)

# =========================
# زر: المهام (يدعم جميع تسميات الأزرار باللغات المتاحة)
# =========================
@bot.message_handler(func=lambda m: m.text in ALL_TASK_LABELS)
def send_task(message):
    account = get_account()
    if account is None:
        return bot.send_message(message.chat.id, L(message.from_user, "no_accounts"))

    first, last, email, password = account
    task_text = L(
        message.from_user,
        "task_details",
        first=first,
        last=last,
        email=email,
        password=password
    )

    user_pending_task[message.chat.id] = True
    append_csv_row(PENDING_FILE, [str(message.chat.id), task_text])
    bot.send_message(message.chat.id, task_text)

# =========================
# زر: رابط الإحالة
# =========================
@bot.message_handler(func=lambda m: m.text in ALL_REF_LABELS)
def send_ref_link(message):
    bot_username = bot.get_me().username or "your_bot"
    ref_token = f"ref{message.from_user.id}"
    referral_link = f"https://t.me/{bot_username}?start={quote_plus(ref_token)}"
    note = L(message.from_user, "ref_link_note")
    bot.send_message(message.chat.id, f"{L(message.from_user, 'ref')}:\n{referral_link}\n\n{note}")

# =========================
# زر: رصيدي
# =========================
@bot.message_handler(func=lambda m: m.text in ALL_BALANCE_LABELS)
def balance_handler(message):
    balance = get_balance(message.chat.id)
    bot.send_message(message.chat.id, L(message.from_user, "balance_msg", bal=f"{balance:.8f}"))

# =========================
# زر: حسابي
# =========================
@bot.message_handler(func=lambda m: m.text in ALL_ACCOUNT_LABELS)
def account_handler(message):
    balance = get_balance(message.chat.id)
    bot.send_message(message.chat.id, L(message.from_user, "account_info", id=message.chat.id, bal=f"{balance:.8f}"))

# =========================
# زر: سحب الأرباح
# =========================
@bot.message_handler(func=lambda m: m.text in ALL_WITHDRAW_LABELS)
def withdraw_handler(message):
    balance = get_balance(message.chat.id)
    if balance < 1:
        bot.send_message(message.chat.id, L(message.from_user, "withdraw_min"))
    else:
        bot.send_message(message.chat.id, L(message.from_user, "withdraw_address"))
        bot.register_next_step_handler(message, get_wallet)

def get_wallet(message):
    wallet = message.text.strip()
    # أرسل طلب السحب للإدمن
    bot.send_message(ADMIN_ID, f"🔔 طلب سحب جديد\nمن: {message.chat.id}\nالمحفظة: {wallet}\nالرصيد: {get_balance(message.chat.id):.8f} USDT")
    bot.send_message(message.chat.id, L(message.from_user, "withdraw_sent"))

# =========================
# رفض الملفات/صور أثناء انتظار إثبات المهمة
# =========================
@bot.message_handler(content_types=['photo','video','document','sticker','animation'])
def reject_proof(message):
    if user_pending_task.get(message.chat.id):
        bot.send_message(message.chat.id, L(message.from_user, "send_text_only"))
    else:
        bot.send_message(message.chat.id, L(message.from_user, "no_pending"))

# =========================
# استلام إثبات المهمة — هذا الهاندلر يعمل فقط إذا المستخدم فعلاً في انتظار
# =========================
@bot.message_handler(func=lambda m: user_pending_task.get(m.chat.id) == True)
def receive_proof(message):
    try:
        bot.send_message(ADMIN_ID, f"📩 إثبات مهمة جديدة\nمن المستخدم: {message.chat.id}\n\nالرسالة:\n{message.text}")
        markup = telebot.types.InlineKeyboardMarkup()
        # Keep admin buttons simple (admin likely uses one language); leave as symbols + arabic labels from original
        markup.add(
            telebot.types.InlineKeyboardButton("✔ قبول", callback_data=f"accept_{message.chat.id}"),
            telebot.types.InlineKeyboardButton("❌ رفض", callback_data=f"reject_{message.chat.id}")
        )
        bot.send_message(ADMIN_ID, "اختار:", reply_markup=markup)
        bot.send_message(message.chat.id, L(message.from_user, "proof_received"))
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
        # send localized message to user (we need a fake user object with language_code)
        # The user's language_code isn't available here; we will attempt to fetch a chat member language by storing language at runtime in a map
        try:
            bot.send_message(uid, "✔ تم قبول المهمة!\n+0.05 USDT")
        except Exception:
            pass
        bot.send_message(ADMIN_ID, "✔ تم القبول.")
    elif data.startswith("reject_"):
        uid_str = data.split("_",1)[1]
        try:
            uid = int(uid_str)
        except:
            uid = uid_str
        try:
            bot.send_message(uid, "❌ تم رفض المهمة.")
        except Exception:
            pass
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
