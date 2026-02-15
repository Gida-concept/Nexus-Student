import logging
import sys
from telegram.ext import Application, CommandHandler
from telegram import Update
from bot.handlers.start import start_command
from bot.handlers.course_advisor import advisor_conversation_handler
from bot.handlers.project import project_conversation_handler
from bot.handlers.assignment import assignment_conversation_handler
from bot.handlers.tutor import tutor_conversation_handler
from bot.handlers.payment import payment_conversation_handler, show_subscription_plans
from bot.handlers.admin import admin_handlers
from bot.config import Config
from bot import app
from bot.models import db

# Configure logging to show on console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the Telegram bot."""
    logger.info("Initializing database...")
    
    # Initialize database
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    logger.info("Building Telegram application...")
    
    # Initialize the Telegram application
    try:
        application = Application.builder().token(Config.BOT_TOKEN).build()
        logger.info("Telegram application built successfully!")
    except Exception as e:
        logger.error(f"Failed to build Telegram application: {e}")
        sys.exit(1)

    # Register command handlers
    logger.info("Registering handlers...")
    application.add_handler(CommandHandler("start", start_command))

    # Register conversation handlers
    application.add_handler(advisor_conversation_handler)
    application.add_handler(project_conversation_handler)
    application.add_handler(assignment_conversation_handler)
    application.add_handler(tutor_conversation_handler)
    application.add_handler(payment_conversation_handler)

    # Register admin handlers
    for handler in admin_handlers:
        application.add_handler(handler)

    logger.info("All handlers registered successfully!")
    
    # Start the bot
    logger.info("Starting Student AI Telegram Bot...")
    logger.info("Bot is now running. Press Ctrl+C to stop.")
    
    try:
        # Run the bot using run_polling
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Bot crashed during runtime: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed during startup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
