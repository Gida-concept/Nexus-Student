from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from bot.models import User, db
from bot import app
from bot.utils.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

@admin_required
async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the admin dashboard with key metrics."""
    query = update.callback_query
    await query.answer()
    with app.app_context():
        total_users = User.query.count()

    keyboard = [
        [InlineKeyboardButton("👥 User Management", callback_data="ADMIN_USERS")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🏠 **Admin Dashboard**\n\n📊 **System Overview**\nTotal Users: {total_users}\n\nWhat would you like to manage?", reply_markup=reply_markup, parse_mode='Markdown')

@admin_required
async def handle_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user management commands."""
    query = update.callback_query
    await query.answer()
    with app.app_context():
        users = User.query.order_by(User.created_at.desc()).limit(10).all()
    if not users:
        await query.edit_message_text("No users found in the system.")
        return
    user_list = "\n".join(f"{i+1}. @{user.username or 'N/A'} (ID: {user.telegram_id})" for i, user in enumerate(users))
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin Dashboard", callback_data="ADMIN_DASHBOARD")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"👥 **Recent Users**\n\n{user_list}\n\nUse /admin_user [ID] to manage a user.", reply_markup=reply_markup)

admin_handlers = [
    CallbackQueryHandler(admin_dashboard, pattern="^MENU_ADMIN$"),
    CallbackQueryHandler(admin_dashboard, pattern="^ADMIN_DASHBOARD$"),
    CallbackQueryHandler(handle_admin_users, pattern="^ADMIN_USERS$"),
]
