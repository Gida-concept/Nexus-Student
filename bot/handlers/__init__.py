from telegram.ext import Application, CallbackQueryHandler
from .start import start_command
from .course_advisor import advisor_conversation_handler
from .project import project_conversation_handler
from .assignment import assignment_conversation_handler
from .tutor import tutor_conversation_handler
from .admin import admin_handlers

def setup_handlers(application: Application):
    """Set up all handlers for the Telegram bot application."""
    # Command handlers
    application.add_handler(start_command)

    # Conversation handlers
    application.add_handler(advisor_conversation_handler)
    application.add_handler(project_conversation_handler)
    application.add_handler(assignment_conversation_handler)
    application.add_handler(tutor_conversation_handler)

    # Admin handlers
    for handler in admin_handlers:
        application.add_handler(handler)

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(
        start_command,
        pattern="^MENU_"
    ))
