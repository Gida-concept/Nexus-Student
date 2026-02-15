from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from bot.models import User, PricingPlan, Subscription
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
        active_subscribers = Subscription.query.filter_by(status='active').count()
        active_plans = PricingPlan.query.filter_by(is_active=True).count()
        payment_status = "ENABLED" if context.bot_data.get('ENABLE_PAYMENTS', True) else "DISABLED"
    keyboard = [
        [InlineKeyboardButton("👥 User Management", callback_data="ADMIN_USERS")],
        [InlineKeyboardButton("💰 Pricing Plans", callback_data="ADMIN_PRICING")],
        [InlineKeyboardButton("🔄 Payment Settings", callback_data="ADMIN_PAYMENTS")],
        [InlineKeyboardButton("📊 System Stats", callback_data="ADMIN_STATS")],
        [InlineKeyboardButton("❌ Close", callback_data="ADMIN_CLOSE")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"🏠 **Admin Dashboard**\n\n📊 **System Overview**\nTotal Users: {total_users}\nActive Subscribers: {active_subscribers}\nActive Plans: {active_plans}\nPayment System: {payment_status}\n\nWhat would you like to manage?", reply_markup=reply_markup)

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
    user_list = "\n".join(f"{i+1}. {user.username or 'Anonymous'} (ID: {user.telegram_id})" for i, user in enumerate(users))
    keyboard = [[InlineKeyboardButton("🔙 Back to Dashboard", callback_data="ADMIN_DASHBOARD")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"👥 **Recent Users**\n\n{user_list}\n\nUse /admin_user [ID] to view details or manage a specific user.", reply_markup=reply_markup)

@admin_required
async def handle_admin_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pricing plan management."""
    query = update.callback_query
    await query.answer()
    with app.app_context():
        plans = PricingPlan.query.all()
    if not plans:
        await query.edit_message_text("No pricing plans configured.")
        return
    plan_list = "\n".join(f"{i+1}. {plan.name} - ₦{plan.price/100:.2f} ({plan.interval})" for i, plan in enumerate(plans))
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="ADMIN_DASHBOARD")],
        [InlineKeyboardButton("💰 Sync Plans", callback_data="ADMIN_SYNC_PLANS")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"💰 **Pricing Plans**\n\n{plan_list}\n\nUse /admin_plan [ID] to edit a specific plan.", reply_markup=reply_markup)

@admin_required
async def handle_admin_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment system settings."""
    query = update.callback_query
    await query.answer()
    current_status = context.bot_data.get('ENABLE_PAYMENTS', True)
    keyboard = [
        [InlineKeyboardButton("🔄 Toggle Payment System", callback_data=f"TOGGLE_PAYMENTS_{not current_status}")],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="ADMIN_DASHBOARD")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    status_text = "ENABLED" if current_status else "DISABLED"
    await query.edit_message_text(f"💳 **Payment System Settings**\n\nCurrent Status: {status_text}\n\nToggle the payment system on/off globally.", reply_markup=reply_markup)

@admin_required
async def toggle_payment_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle the payment system on/off."""
    query = update.callback_query
    await query.answer()
    new_status = query.data.split("_")[-1].lower() == "true"
    context.bot_data['ENABLE_PAYMENTS'] = new_status
    status_text = "ENABLED" if new_status else "DISABLED"
    await query.edit_message_text(f"✅ Payment system has been {status_text}.\n\nThis change will take effect immediately.")

@admin_required
async def close_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close the admin menu."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Admin menu closed.")

admin_handlers = [
    CommandHandler("admin", admin_dashboard),
    CallbackQueryHandler(admin_dashboard, pattern="^ADMIN_DASHBOARD$"),
    CallbackQueryHandler(handle_admin_users, pattern="^ADMIN_USERS$"),
    CallbackQueryHandler(handle_admin_pricing, pattern="^ADMIN_PRICING$"),
    CallbackQueryHandler(handle_admin_payments, pattern="^ADMIN_PAYMENTS$"),
    CallbackQueryHandler(handle_admin_payments, pattern="^ADMIN_STATS$"),
    CallbackQueryHandler(toggle_payment_system, pattern="^TOGGLE_PAYMENTS_"),
    CallbackQueryHandler(close_admin_menu, pattern="^ADMIN_CLOSE$")
]
