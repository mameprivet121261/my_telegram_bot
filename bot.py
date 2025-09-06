import os
import json
import random
from datetime import datetime
from PIL import Image
import io
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, request

# Переменные окружения
TOKEN = os.getenv("BOT_TOKEN")
SECRET_CODE = os.getenv("SECRET_CODE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: https://yourapp.onrender.com/<TOKEN>

IMAGE_FOLDER = "images"
AUTH_FILE = "/tmp/authorized.json"

# Случайные тексты
RANDOM_TEXTS = [
    "'Любовь не знает ни меры, ни цены' Эрих Мария Ремарк",
    "'Самое лучшее во мне — это ты'",
    "'Иногда человек, которого вы любите, просто не понимает, как сильно вы его любите'",
    "'Жизнь измеряется не количеством сделанных вдохов и выдохов, а количеством тех моментов, когда от счастья захватывает дух'",
    "'Есть одна боль, которую я часто чувствую, и ты никогда её не узнаешь. Это боль от отсутствия тебя' Дэвид Грейсон",
    "'Любовь не терпит объяснений. Ей нужны поступки'  Эрих Мария Ремарк",
    "'Любить — это не значит смотреть друг на друга, любить — значит вместе смотреть в одном направлении' Антуан де Сент-Экзюпери",
    "'Человек, которому вы нужны, всегда найдет способ быть рядом'  Михаил Лермонтов",
    "'Настоящие любовные истории никогда не заканчиваются' Ричард Бах",
    "'Любовь – это купание, нужно либо нырять с головой, либо вообще не лезть в воду. Если будешь слоняться вдоль берега по колено в воде, то тебя только обрызгает брызгами и ты будешь мерзнуть и злиться' Сергей Есенин",
    "'Ответная любовь тех, кого мы любим, — это огонь, питающий нашу жизнь' Пабло Неруда",
    "'Разлука для любви то же, что ветер для огня: маленькую любовь она тушит, а большую раздувает еще сильней'  Александр Куприн",
    "'Любящее сердце стоит больше, чем вся мудрость на свете'   Чарльз Диккенс",
    "'Любовь — это одна душа в двух телах'  Аристотель",
    "'Люби всех, доверься немногим, не делай зла никому'  Уильям Шекспир",
	"'Из чего сделаны наши души, его и моя одинаковы'   Эмили Бронте",
	"'Любовь — это всё и даже больше.'   Эдвард Эстлин Каммингс",
	"'Я твой, не возвращай меня себе.'   Руми",
	"'Любовь — дым, поднятый из вздохов.'   Шекспир",
	"'Я любил её вопреки разуму, обещаниям и покою.'   Чарльз Диккенс",
	"'В любви всегда один целует, а другой подставляет щёку.'   французская пословица",
	"'Любовь не меняется с часами и неделями, но выдерживает даже до конца времён.'   Шекспир",
	"'Любовь — это бесконечная тайна.'   Рабиндранат Тагор",
	"'Мы любили любовью, которая была больше чем любовь.'   Эдгар Аллан По",
	"'Любить себя — начало романа на всю жизнь.'   Оскар Уайльд",
	"'У сердца есть свои причины, которых не знает разум.'   Блез Паскаль",
    "'Нет лекарства от любви, кроме как любить ещё сильнее.'  Генри Дэвид Торо",
	"'Любовь — это пространство и время, измеренные сердцем.'   Марсель Пруст",
	"'Любовь — это дружба, охваченная огнём.'   Джереми Тейлор",
	"'Если я знаю, что такое любовь, то только благодаря тебе.'   Герман Гессе",
	"'Любовь не властвует, она взращивает.'   Иоганн Вольфганг Гёте",
	"'Любовь — поэзия чувств.'   Оноре де Бальзак",
	"'Истории истинной любви не имеют конца.'   Ричард Бах",
	"'Любовь смотрит не глазами, а разумом.'   Шекспир",
	"'Любовь — это холст природы, вышитый воображением.'  Вольтер",
	"'Любить и быть любимым — значит чувствовать солнце с обеих сторон.'   Дэвид Вискотт",
	"'Любовь — единственное золото.'   Альфред Теннисон",
]

# Работа с авторизованными пользователями
def load_authorized():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_authorized(users):
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

authorized_users = load_authorized()

# Случайное изображение без повторов
LAST_IMAGE = {}
def get_random_image(user_id):
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        return None
    prev = LAST_IMAGE.get(user_id)
    choices = [f for f in files if f != prev] or files
    chosen = random.choice(choices)
    LAST_IMAGE[user_id] = chosen
    return os.path.join(IMAGE_FOLDER, chosen)

# Случайный текст без повторов
LAST_TEXT = {}
def get_random_text(user_id):
    prev = LAST_TEXT.get(user_id)
    choices = [t for t in RANDOM_TEXTS if t != prev] or RANDOM_TEXTS
    chosen = random.choice(choices)
    LAST_TEXT[user_id] = chosen
    return chosen

# Отправка фото без переворота, с ресайзом если слишком большое
async def send_safe_photo(update, image_path, caption=""):
    try:
        with Image.open(image_path) as img:
            MAX_WIDTH = 2000
            MAX_HEIGHT = 2000
            if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
                ratio = min(MAX_WIDTH / img.width, MAX_HEIGHT / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            await update.message.reply_photo(photo=img_bytes, caption=caption)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка с изображением: {e}")

# Главное меню
async def show_main_menu(message):
    keyboard = [["📸Тык🙃"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await message.reply_text("тыкни!!! ⬇️", reply_markup=reply_markup)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in authorized_users:
        await show_main_menu(update.message)
    else:
        await update.message.reply_text("🔑 Введи секретный код для доступа:")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if user_id not in authorized_users:
        if text == SECRET_CODE:
            authorized_users[user_id] = {"count": 0, "last_date": ""}
            save_authorized(authorized_users)
            await update.message.reply_text("Танюш, это ты?))))❤️")
            await show_main_menu(update.message)
        else:
            await update.message.reply_text("подумай лучше!")
        return

    if text == "📸Тык🙃":
        today = datetime.now().strftime("%Y-%m-%d")
        user_data = authorized_users[user_id]
        if user_data["last_date"] != today:
            user_data["count"] = 0
            user_data["last_date"] = today
        if user_data["count"] >= 2:
            await update.message.reply_text("🥺 На сегодня всё, пупсик")
            return
        user_data["count"] += 1
        save_authorized(authorized_users)

        image_path = get_random_image(user_id)
        caption = get_random_text(user_id)
        if image_path:
            await send_safe_photo(update, image_path, caption)
        else:
            await update.message.reply_text("❌ Ошибка: нет картинок в папке!")
    else:
        await update.message.reply_text("Нажми кнопку ⬇️")

# Flask для вебхука
flask_app = Flask(__name__)
app = Application.builder().token(TOKEN).build()

# Роут для вебхука
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app.bot)
    app.update_queue.put(update)
    return "OK"

@flask_app.route("/")
def index():
    return "Bot is running!"

# Добавляем обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Устанавливаем вебхук
app.bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)