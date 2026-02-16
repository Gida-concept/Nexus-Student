import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from bot.config import Config
from bot import app  # Imports the Flask app context from bot/__init__.py
from bot.models import db

# Import all handlers directly
from bot.handlers.start import start_command
from bot.handlers.course_advisor import advisor_conversation_handler
from bot.handlers.project import project_conversation_handler
from bot.handlers.assignment import assignment_conversation_handler
from bot.handlers.tutor import tutor_conversation_handler
from bot.handlers.admin import admin_handlers
from bot.handlers.help import help_command

# Configure logging to show on the console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the Telegram bot."""
    logger.info("Initializing database...")
    try:
        # Use the app context to create the database tables
        with app.app_context():
            db.create_all()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("Building Telegram application...")
    application = Application.builder().token(Config.BOT_TOKEN).build()

    # --- Handler Registration ---
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))

    # Conversation handlers for each feature
    application.add_handler(advisor_conversation_handler)
    application.add_handler(project_conversation_handler)
    application.add_handler(assignment_conversation_handler)
    application.add_handler(tutor_conversation_handler)

    # Admin handlers
    for handler in admin_handlers:
        application.add_handler(handler)

    # Simple callback handlers
    application.add_handler(CallbackQueryHandler(help_command, pattern="^MENU_HELP$"))
    application.add_handler(CallbackQueryHandler(start_command, pattern="^BACK_TO_MENU$"))

    logger.info("All handlers registered successfully!")
    logger.info("Starting Student AI Telegram Bot... Press Ctrl+C to stop.")
    
    # This runs the bot and blocks until you stop it
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot crashed during startup: {e}")
        import traceback
        traceback.print_exc()
