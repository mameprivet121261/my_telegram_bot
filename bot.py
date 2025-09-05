import os
import json
import random
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flask import Flask
import threading


# Загружаем .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
SECRET_CODE = os.getenv("SECRET_CODE")

# Папка с картинками
IMAGE_FOLDER = "images"


AUTH_FILE = "/tmp/authorized.json"


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

# Функции для работы с авторизованными пользователями


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
    images = []

    for f in files:
        path = os.path.join(IMAGE_FOLDER, f)
        if f.lower().endswith((".jpg", ".jpeg", ".png")):
            images.append(path)

    if not images:
        return None
    return random.choice(images)


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


# Проверка кода
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    if user_id in authorized_users:
        return

    if text == SECRET_CODE:
        authorized_users[user_id] = {"count": 0, "last_date": ""}
        save_authorized(authorized_users)
        await update.message.reply_text("Танюш, это ты?))))❤️")
        await show_main_menu(update.message)
    else:
        await update.message.reply_text("🚫 Неверный код!")


# Главное меню
async def show_main_menu(message):
    keyboard = [[InlineKeyboardButton("📸Пук🙃", callback_data="combo")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Выбери действие ⬇️", reply_markup=reply_markup)


# Обработка кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if user_id not in authorized_users:
        await query.answer("🚫 Нет доступа!")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    user_data = authorized_users[user_id]

    if user_data["last_date"] != today:
        user_data["count"] = 0
        user_data["last_date"] = today

    if user_data["count"] >= 2:
        await query.message.reply_text("🥺 На сегодня всё, пупсик")
        return

    user_data["count"] += 1
    save_authorized(authorized_users)

    await query.answer()

    if query.data == "combo":
        image_path = get_random_image()
        text = get_random_text()
        if image_path:
            with open(image_path, "rb") as photo:
                await query.message.reply_photo(photo=photo, caption=text)
        else:
            await query.message.reply_text("❌ В папке images нет картинок!")


# Запуск бота
def main():
    app = Application.builder() \
        .token(TOKEN) \
        .connect_timeout(30) \
        .read_timeout(30) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))
    app.add_handler(CallbackQueryHandler(button_handler))

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
    # запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    # запускаем Telegram бота
    main()