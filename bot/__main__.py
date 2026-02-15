import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.handlers import (
    start,
    course_advisor,
    project,
    assignment,
    tutor,
    payment,
    admin
)
from bot.handlers.__init__ import advisor_conversation_handler
from bot.handlers.project import project_conversation_handler
from bot.handlers.assignment import assignment_conversation_handler
from bot.handlers.tutor import tutor_conversation_handler
from bot.handlers.payment import payment_conversation_handler
from bot.handlers.admin import admin_handlers
from bot.config import Config
from bot import db_app
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the Telegram bot."""
    # Initialize the Telegram application
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # Initialize database
    with db_app.app_context():
        # Create tables if they don't exist
        db_app.create_all()

    # Register command handlers
    application.add_handler(CommandHandler("start", start.start_command))

    # Register conversation handlers
    application.add_handler(advisor_conversation_handler)
    application.add_handler(project_conversation_handler)
    application.add_handler(assignment_conversation_handler)
    application.add_handler(tutor_conversation_handler)
    application.add_handler(payment_conversation_handler)

    # Register admin handlers
    for handler in admin_handlers:
        application.add_handler(handler)

    # Register callback query handlers
    application.add_handler(CallbackQueryHandler(
        start.start_command,
        pattern="^MENU_"
    ))

    # Start the bot
    logger.info("Starting Student AI Telegram Bot...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")