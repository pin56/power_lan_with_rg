import os 
from dotenv import load_dotenv
import asyncio
import time
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

from wol import send_wol, send_off, send_sleep
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from listen_time import run_udp_port_listener_time


load_dotenv()

pc_mac_address = os.getenv("PC_MAC_ADDRESS")
broadcast_ip = os.getenv("BROADCAST_IP")
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
users_env = os.getenv("USERS")

PORT = int(os.getenv('PORT'))
ETHERNET = os.getenv('ETHERNET')

ALLOWED_USERS = []
users_env = str(users_env)[1:-1]
users_env = users_env.split(',')
for i in users_env:
    ALLOWED_USERS.append(int(i))

print(f"Разрешенные пользователи: {ALLOWED_USERS}")
logger.info(f"Разрешенные пользователи: {ALLOWED_USERS}")



button_PC_control_data =    [[InlineKeyboardButton("🚀 turn on", callback_data="turn_on")], 
                            [InlineKeyboardButton("⚫️ turn off", callback_data="turn_off")],
                            [InlineKeyboardButton("🛏️ sleep", callback_data="sleep")]]

# Для хранения активных пользователей (кто запускал /start или нажимал кнопки)
active_users = {}

# Глобальный статус ПК
PC_status = '⚫️ Выключен'
last_packet_time = 0

def is_user_authorized(user_id: int) -> bool:
    """Проверяет, авторизован ли пользователь."""
    logger.info(f'Проверка авторизации пользователя: {user_id}, список: {ALLOWED_USERS}')
    return user_id in ALLOWED_USERS

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} вызвал /start")
    if not is_user_authorized(user.id):
        logger.warning(f"Доступ запрещен для пользователя {user.id}")
        await update.message.reply_html(
            f"❌ Доступ запрещен! Ваш ID: {user.id}\n"
            f"Обратитесь к администратору для получения доступа."
        )
        return
    # Сохраняем пользователя как активного
    active_users[user.id] = {'query': update.message}
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=InlineKeyboardMarkup(button_PC_control_data),
    )
    logger.info(f"Пользователь {user.id} добавлен в активные")

async def listen_time_forever(context):
    global PC_status, last_packet_time
    loop = asyncio.get_running_loop()
    while True:
        # run_udp_port_listener_time блокирующая, поэтому в executor
        data, _ = await loop.run_in_executor(
            None, run_udp_port_listener_time, PORT, ETHERNET
        )
        try:
            data_dict = json.loads(data.decode('utf-8'))
            formatted_uptime = data_dict.get('formatted_uptime', 'N/A')
        except Exception as e:
            logger.error(f"Ошибка при обработке данных UDP: {e}")
            data_dict = {}
            formatted_uptime = 'N/A'
        last_packet_time = time.time()
        if PC_status != '🚀 Включен':
            PC_status = '🚀 Включен'
            logger.info(f"ПК включился. Статус обновлен: {PC_status}")
            # ПК включился — уведомить всех активных пользователей
            for user_id, msg_ctx in active_users.items():
                try:
                    await msg_ctx['query'].edit_message_text(
                        text=f"status: {PC_status}\nвремя работы: {formatted_uptime}",
                        reply_markup=InlineKeyboardMarkup(button_PC_control_data),
                    )
                    logger.info(f"Пользователь {user_id} уведомлен о включении ПК")
                except Exception as e:
                    logger.error(f"Ошибка при уведомлении пользователя {user_id}: {e}")
        else:
            # ПК уже включён — просто обновить время
            for user_id, msg_ctx in active_users.items():
                try:
                    await msg_ctx['query'].edit_message_text(
                        text=f"status: {PC_status}\nвремя работы: {formatted_uptime}",
                        reply_markup=InlineKeyboardMarkup(button_PC_control_data),
                    )
                except Exception as e:
                    logger.error(f"Ошибка при обновлении времени для пользователя {user_id}: {e}")

async def pc_status_timeout_checker(context, timeout=10):
    global PC_status, last_packet_time
    while True:
        await asyncio.sleep(2)
        if PC_status == '🚀 Включен' and (time.time() - last_packet_time > timeout):
            PC_status = '⚫️ Выключен'
            logger.info(f"ПК выключен по таймауту. Статус обновлен: {PC_status}")
            for user_id, msg_ctx in active_users.items():
                try:
                    await msg_ctx['query'].message.reply_html(
                        text=f"status: {PC_status}",
                        reply_markup=InlineKeyboardMarkup(button_PC_control_data),
                    )
                    logger.info(f"Пользователь {user_id} уведомлен о выключении ПК")
                except Exception as e:
                    logger.error(f"Ошибка при уведомлении пользователя {user_id} о выключении: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    logger.info(f"Пользователь {user_id} нажал кнопку: {query.data}")
    # Сохраняем пользователя как активного
    active_users[user_id] = {'query': query}
    if query.data == "turn_on":
        send_wol(pc_mac_address, broadcast_ip)
        logger.info(f"Отправлен WOL для ПК {pc_mac_address}")
        await query.answer()
    elif query.data == "turn_off":
        await query.answer()
        send_off(pc_mac_address, broadcast_ip)
        logger.info(f"Отправлен сигнал выключения для ПК {pc_mac_address}")
    elif query.data == "sleep":
        await query.answer()
        send_sleep(pc_mac_address, broadcast_ip)
        logger.info(f"Отправлен сигнал сна для ПК {pc_mac_address}")
    # Не обновляем статус вручную — это делает слушатель

async def post_init(app):
    app.create_task(listen_time_forever(app))
    app.create_task(pc_status_timeout_checker(app))

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_bot_token).build()
    logger.info("Бот Telegram инициализирован")
    print(str(application)[:-10])

    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Запускаем фоновый слушатель и таймаут-детектор
    application.post_init = post_init

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Бот Telegram запущен (polling)")


if __name__ == "__main__":
    main()