from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import PricingPlan
from bot.services.payment_service import get_payment_link
from bot import app  # Import for DB context
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
        await query.edit_message_text("🔒 Payments are currently disabled for maintenance.")
        return ConversationHandler.END

    with app.app_context():
        plans = PricingPlan.query.filter_by(is_active=True).all()

    if not plans:
        await query.edit_message_text("No subscription plans are currently available. Please check back later.")
        return ConversationHandler.END

    keyboard = []
    for plan in plans:
        price_ngn = plan.price / 100
        label = f"{plan.name} - ₦{price_ngn:,.0f} ({plan.interval.title()})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"SELECTPLAN_{plan.id}")])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="CANCEL_PAYMENT")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "💎 **Choose Your Plan**\n\n"
        "Select a subscription plan to unlock all premium features.",
        reply_markup=reply_markup
    )
    return

async def start_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the conversation. Triggered when a user clicks a specific plan."""
    query = update.callback_query
    await query.answer()

    if query.data == "CANCEL_PAYMENT":
        await query.edit_message_text("Subscription process cancelled.")
        return ConversationHandler.END

    plan_id = int(query.data.split("_")[1])

    with app.app_context():
        plan = PricingPlan.query.get(plan_id)
        if not plan:
            await query.edit_message_text("⚠️ Invalid plan selected. Please start over.")
            return ConversationHandler.END

        # Store the plan in the context for the next step
        context.user_data['selected_plan'] = plan

    await query.edit_message_text(
        f"📧 **Email Required for {plan.name}**\n\n"
        "To generate the payment link, please provide your email address. "
        "This is where your payment receipt will be sent.",
    )

    return WAITING_FOR_EMAIL

async def capture_email_and_generate_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captures the user's email, validates it, and generates the Paystack link."""
    email = update.message.text.strip()
    
    # Simple email validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text("❌ That doesn't look like a valid email address. Please try again.")
        return WAITING_FOR_EMAIL

    plan = context.user_data.get('selected_plan')
    telegram_id = update.effective_user.id

    if not plan:
        await update.message.reply_text("⚠️ Your session has expired. Please select a plan again from the menu.")
        return ConversationHandler.END

    await update.message.reply_text("⏳ Generating secure payment link...")

    payment_url = get_payment_link(telegram_id, plan.paystack_plan_code, email)

    await update.message.reply_text("💳 **Payment Page Ready**\n\nClick the secure link below to complete your subscription.", reply_markup=None)
    keyboard = [[InlineKeyboardButton("Pay Now", url=payment_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👇 Complete Payment Below", reply_markup=reply_markup)

    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation at any state."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Subscription process cancelled.")
    else:
        await update.message.reply_text("Subscription process cancelled.")
    
    context.user_data.clear()
    return ConversationHandler.END

payment_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_plan_selection, pattern="^SELECTPLAN_")],
    states={
        WAITING_FOR_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_email_and_generate_link)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_conversation),
        CallbackQueryHandler(cancel_conversation, pattern="^CANCEL_PAYMENT$")
    ],
    conversation_timeout=300
)
