import os
import sys
import signal
import asyncio
import django
from django.core.management.base import BaseCommand
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from user_data.models import UserData

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

load_dotenv()


class Command(BaseCommand):
    help = "Run Telegram bot with proper async handling"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = None
        self.loop = None
        self.shutdown_event = asyncio.Event()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user, created = await UserData.objects.aget_or_create(
            id=user_id,
            defaults={
                "first_name": update.effective_user.first_name or "",
                "last_name": update.effective_user.last_name or "",
                "user_name": update.effective_user.username or "",
            },
        )
        response = "Welcome!" if created else f"Welcome back {user.first_name}!"
        await update.message.reply_text(response)

    async def run_bot(self):
        """Main async bot runner with proper cleanup"""
        self.application = (
            Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
        )
        self.application.add_handler(CommandHandler("start", self.start))

        self.stdout.write(self.style.SUCCESS("✅ Bot starting..."))
        async with self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            # Keep running until shutdown signal
            await self.shutdown_event.wait()

            # Proper cleanup
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    def handle(self, *args, **options):
        """Synchronous entry point"""
        # Set up event loop and signal handlers
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Register signal handlers
        for signame in ("SIGINT", "SIGTERM"):
            self.loop.add_signal_handler(
                getattr(signal, signame),
                lambda: self.loop.call_soon_threadsafe(self.shutdown_event.set),
            )

        try:
            self.loop.run_until_complete(self.run_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n🛑 Received shutdown signal"))
        finally:
            if not self.loop.is_closed():
                self.loop.close()
            self.stdout.write(self.style.SUCCESS("⏹️ Bot stopped"))
