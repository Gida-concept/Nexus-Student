from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot import app
from bot.models import User
from bot.config import Config

def admin_required(func):
    """Decorator to restrict access to the admin only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != Config.ADMIN_USER_ID:
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text("⛔ Access Denied. This command is for administrators only.")
            else:
                await update.message.reply_text("⛔ Access Denied. This command is for administrators only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
