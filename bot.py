import os
import sys
import django
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from user_data.models import UserData
from dotenv import load_dotenv


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_telegram_bot.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

load_dotenv()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user, created = await UserData.objects.aget_or_create(
        id=user_id,
        defaults={
            "first_name": update.effective_user.first_name or "",
            "last_name": update.effective_user.last_name or "",
            "user_name": update.effective_user.username or "",
        },
    )

    if created:
        await update.message.reply_text("Welcome to django-telegram bot!")
    else:
        await update.message.reply_text(f"Welcome back {user.first_name}!")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))

    print("Bot started...")
    application.run_polling()


if __name__ == "__main__":
    main()
