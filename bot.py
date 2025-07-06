import os 
from dotenv import load_dotenv

from wol import send_wol
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes


load_dotenv()

pc_mac_address = os.getenv("PC_MAC_ADDRESS")
broadcast_ip = os.getenv("BROADCAST_IP")
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
users_env = os.getenv("USERS")


ALLOWED_USERS = []
users_env = str(users_env)[1:-1]
users_env = users_env.split(',')
for i in users_env:
    ALLOWED_USERS.append(int(i))

print(f"Разрешенные пользователи: {ALLOWED_USERS}")



button_data = [[InlineKeyboardButton("🚀 turn on", callback_data="turn_on")], 
                [InlineKeyboardButton("⚫️ turn off", callback_data="turn_off")]]

def is_user_authorized(user_id: int) -> bool:
    """Проверяет, авторизован ли пользователь."""
    print(f'user_id: {user_id}, list:  {ALLOWED_USERS}')
    return user_id in ALLOWED_USERS

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    if not is_user_authorized(user.id):
        await update.message.reply_html(
            f"❌ Доступ запрещен! Ваш ID: {user.id}\n"
            f"Обратитесь к администратору для получения доступа."
        )
        return
    
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=InlineKeyboardMarkup(button_data),
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    
    # Проверяем авторизацию пользователя
    if not is_user_authorized(user.id):
        await query.answer("❌ Доступ запрещен!", show_alert=True)
        return

    if(query.data == "turn_on"):
        send_wol(pc_mac_address, broadcast_ip)
        await query.answer()
        try:
            await query.edit_message_text(
                text=f"🚀 turn on",
                reply_markup=InlineKeyboardMarkup(button_data),
            )
        except Exception as e:
            pass

    elif(query.data == "turn_off"):
        await query.answer()
        try:
            await query.edit_message_text(
                text=f"⚫️ turn off",
                reply_markup=InlineKeyboardMarkup(button_data),
            )
        except Exception as e:
            pass

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(telegram_bot_token).build()
    print(str(application)[:-10])

    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()