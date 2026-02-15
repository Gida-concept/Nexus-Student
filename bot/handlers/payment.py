from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import PricingPlan, Subscription, db
from bot.services.payment_service import get_payment_link
from bot import app
from bot.config import Config
import logging
import re

logger = logging.getLogger(__name__)

SELECTING_PLAN, WAITING_FOR_EMAIL = range(2)

async def show_subscription_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays available subscription plans as a response to a menu click."""
    query = update.callback_query
    await query.answer()
    
    if not Config.ENABLE_PAYMENTS:
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔒 Payments are currently disabled for maintenance.", reply_markup=reply_markup)
        return ConversationHandler.END

    with app.app_context():
        plans = PricingPlan.query.filter_by(is_active=True).all()

    if not plans:
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("No subscription plans are currently available. Please check back later.", reply_markup=reply_markup)
        return ConversationHandler.END

    keyboard = []
    for plan in plans:
        price_ngn = plan.price / 100
        label = f"{plan.name} - ₦{price_ngn:,.0f} ({plan.interval.title()})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"SELECTPLAN_{plan.id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "💎 **Choose Your Plan**\n\n"
        "Select a subscription plan to unlock all premium features.",
        reply_markup=reply_markup
    )
    return SELECTING_PLAN

async def start_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the conversation. Triggered when a user clicks a specific plan."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "BACK_TO_MENU":
        return ConversationHandler.END
        
    plan_id = int(query.data.split("_")[1])

    with app.app_context():
        plan = PricingPlan.query.get(plan_id)
        if not plan:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("⚠️ Invalid plan selected. Please start over.", reply_markup=reply_markup)
            return ConversationHandler.END

        # Store the plan in the context for the next step
        context.user_data['selected_plan'] = plan

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📧 **Email Required for {plan.name}**\n\n"
        "To generate the payment link, please provide your email address. "
        "This is where your payment receipt will be sent.",
        reply_markup=reply_markup
    )

    return WAITING_FOR_EMAIL

async def capture_email_and_generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captures the user's email, validates it, and generates the Paystack link."""
    email = update.message.text.strip()
    
    # Basic email validation regex
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Please enter a valid email address (e.g., user@gmail.com).")
        return WAITING_FOR_EMAIL

    plan = context.user_data.get('selected_plan')
    telegram_id = update.effective_user.id

    if not plan:
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ Your session has expired. Please select a plan again from the menu.", reply_markup=reply_markup)
        return ConversationHandler.END

    await update.message.reply_text("⏳ Generating secure payment link...")

    # Generate payment link using our pricing from database
    # Note: We're now passing the amount directly instead of plan_code
    payment_url = get_payment_link(
        telegram_id=telegram_id,
        amount=plan.price,  # Pass amount directly in kobo
        user_email=email,
        plan_name=plan.name
    )

    if payment_url:
        keyboard = [
            [InlineKeyboardButton("💳 Pay Now (Secure Link)", url=payment_url)],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ **Link Ready!**\n\n"
            "Click the button below to complete your payment on Paystack's secure page. "
            "Your access will be upgraded automatically once the payment is confirmed.",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ Could not connect to the payment gateway. Please try again later.", reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the payment conversation."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("Payment process cancelled.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Payment process cancelled.")
        
    context.user_data.clear()
    return ConversationHandler.END

payment_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(show_subscription_plans, pattern="^MENU_SUBSCRIBE$")],
    states={
        SELECTING_PLAN: [CallbackQueryHandler(start_plan_selection, pattern="^SELECTPLAN_|BACK_TO_MENU$")],
        WAITING_FOR_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_email_and_generate_link)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_payment),
        CallbackQueryHandler(cancel_payment, pattern="^CANCEL_PAYMENT$")
    ],
    conversation_timeout=300
)
