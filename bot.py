import os
import json
import random
from datetime import datetime
from PIL import Image
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup
from flask import Flask
import threading

# Переменные окружения (Render)
TOKEN = os.getenv("BOT_TOKEN")
SECRET_CODE = os.getenv("SECRET_CODE")

# Папка с картинками
IMAGE_FOLDER = "images"

# Файл для хранения авторизованных пользователей (Render разрешает запись только в /tmp)
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

# Случайное изображение
def get_random_image():
    if not os.path.exists(IMAGE_FOLDER):
        return None
    files = os.listdir(IMAGE_FOLDER)
    images = [os.path.join(IMAGE_FOLDER, f) for f in files if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    return random.choice(images) if images else None

# Функция для безопасной отправки фото
async def send_safe_photo(update, image_path, caption=""):
    try:
        with Image.open(image_path) as img:
            # Ограничение максимальной высоты и ширины
            MAX_DIMENSION = 2000  # px
            if img.height > MAX_DIMENSION or img.width > MAX_DIMENSION:
                ratio = min(MAX_DIMENSION / img.width, MAX_DIMENSION / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            # Сохраняем в память в формате JPEG
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            await update.message.reply_photo(photo=img_bytes, caption=caption)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка с изображением: {e}")


# Случайный текст
def get_random_text():
    return random.choice(RANDOM_TEXTS)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id in authorized_users:
        await show_main_menu(update.message)
    else:
        await update.message.reply_text("🔑 Введи секретный код для доступа:")


# Главное меню с кнопкой внизу
async def show_main_menu(message):
    keyboard = [["📸Пук🙃"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=False
    )
    await message.reply_text("тыкни!!! ⬇️", reply_markup=reply_markup)


# Обновленный блок обработки кнопки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if user_id not in authorized_users:
        # Проверяем секретный код
        if text == SECRET_CODE:
            authorized_users[user_id] = {"count": 0, "last_date": ""}
            save_authorized(authorized_users)
            await update.message.reply_text("Танюш, это ты?))))❤️")
            await show_main_menu(update.message)
        else:
            await update.message.reply_text("подумай лучше!")
        return

    # Обработка кнопки
    if text == "📸Пук🙃":
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

        # Получаем случайное изображение
        image_path = get_random_image()
        caption = get_random_text()
        if image_path:
            await send_safe_photo(update, image_path, caption)
        else:
            await update.message.reply_text("❌ Ошибка: нет картинок в папке!")
    else:
        # Сообщение не кнопка
        await update.message.reply_text("Нажми кнопку ⬇️")


# Запуск Telegram бота
def run_telegram_bot():
    app = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен. Жми /start в Telegram")
    app.run_polling()

# Flask dummy сервер для Render
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    # Telegram бот
    run_telegram_bot()