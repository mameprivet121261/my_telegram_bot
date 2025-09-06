import os
import json
import random
from datetime import datetime
from io import BytesIO
from PIL import Image
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackContext

# Переменные окружения
TOKEN = os.getenv("BOT_TOKEN")
SECRET_CODE = os.getenv("SECRET_CODE")
APP_URL = os.getenv("APP_URL")  # публичный URL проекта на Render

# Папка с картинками
IMAGE_FOLDER = "images"
# Файл авторизации пользователей
AUTH_FILE = "/tmp/authorized.json"

# Максимальный размер изображения
MAX_DIMENSION = 2000  # px

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

# Загрузка и сохранение авторизованных пользователей
def load_authorized():
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_authorized(users):
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

authorized_users = load_authorized()
last_sent_image = {}  # чтобы не отправлять одно и то же фото подряд
last_sent_text = {}

# Получение случайного изображения без повторов
def get_random_image(user_id):
    if not os.path.exists(IMAGE_FOLDER):
        return None
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        return None
    previous = last_sent_image.get(user_id)
    available = [f for f in files if f != previous]
    choice = random.choice(available) if available else random.choice(files)
    last_sent_image[user_id] = choice
    return os.path.join(IMAGE_FOLDER, choice)

# Получение случайного текста без повторов
def get_random_text(user_id):
    previous = last_sent_text.get(user_id)
    available = [t for t in RANDOM_TEXTS if t != previous]
    choice = random.choice(available) if available else random.choice(RANDOM_TEXTS)
    last_sent_text[user_id] = choice
    return choice

# Масштабирование изображения при необходимости
def prepare_image(path):
    img = Image.open(path)
    if img.height > MAX_DIMENSION or img.width > MAX_DIMENSION:
        ratio = min(MAX_DIMENSION / img.width, MAX_DIMENSION / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in authorized_users:
        await show_main_menu(update.message)
    else:
        await update.message.reply_text("🔑 Введи секретный код для доступа:")

# Главное меню
async def show_main_menu(message):
    keyboard = [["📸тЫк🙃"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await message.reply_text("тыкни!!! ⬇️", reply_markup=reply_markup)

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
            await update.message.reply_text("Неверный код, попробуй ещё раз!")
        return

    # Кнопка отправки картинки
    if text == "📸тЫк🙃":
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
            img_bytes = prepare_image(image_path)
            await update.message.reply_photo(photo=img_bytes, caption=caption)
        else:
            await update.message.reply_text("❌ Ошибка: нет картинок в папке!")
    else:
        await update.message.reply_text("Нажми кнопку ⬇️")

# Flask приложение для вебхука
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return "OK"

if __name__ == "__main__":
    # Устанавливаем вебхук
    telegram_app.bot.set_webhook(f"{APP_URL}/{TOKEN}")
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))