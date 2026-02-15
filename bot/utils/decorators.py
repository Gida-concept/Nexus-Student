from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot import db_app  # Import the Flask app from __init__ to get DB context
from bot.models import User
from bot.config import Config


def admin_required(func):
    """Decorator to restrict access to the admin only."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != Config.ADMIN_USER_ID:
            await update.message.reply_text("⛔ Access Denied. This command is for administrators only.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


def subscription_required(func):
    """Decorator to restrict access to premium subscribers only."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        telegram_id = update.effective_user.id

        # We need the Flask application context to perform DB operations
        with db_app.app_context():
            user = User.query.filter_by(telegram_id=telegram_id).first()

            if not user:
                await update.message.reply_text("⚠️ Please use /start to initialize your account.")
                return

            # Check for active subscription using the helper property
            if not user.is_premium:
                await update.message.reply_text(
                    "🔒 **Premium Feature**\n\n"
                    "You need an active subscription to use this command.\n"
                    "Tap /subscribe to upgrade your plan."
                )
                return

        return await func(update, context, *args, **kwargs)

    return wrapper


def payment_maintenance_check(func):
    """Decorator to check if payments are enabled in .env"""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not Config.ENABLE_PAYMENTS:
            await update.message.reply_text("⚠️ The payment system is currently disabled for maintenance.")
            return
        return await func(update, context, *args, **kwargs)

    return wrapper