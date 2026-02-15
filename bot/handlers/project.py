from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Project, ProjectChapter, db
from bot import app
from bot.services.perplexica_service import query_perplexica
from bot.utils.decorators import subscription_required
import logging

logger = logging.getLogger(__name__)

PROJECT_TITLE, PROJECT_TOPIC, PROJECT_PAGE_COUNT, CONFIRM_PROJECT = range(4)
GENERATING_CHAPTER = 5

async def start_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for project creation flow."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 **Create New Project**\n\nLet's create a new academic project. I'll guide you through the process.\n\nFirst, please enter the title of your project:")
    return PROJECT_TITLE

async def get_project_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture project title."""
    context.user_data['project_title'] = update.message.text.strip()
    await update.message.reply_text("Great! Now, please describe the topic of your project in detail:")
    return PROJECT_TOPIC

async def get_project_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture project topic."""
    context.user_data['project_topic'] = update.message.text.strip()

    # Show page count options
    keyboard = [
        [InlineKeyboardButton("5 Pages (3,750 words)", callback_data="5")],
        [InlineKeyboardButton("10 Pages (7,500 words)", callback_data="10")],
        [InlineKeyboardButton("15 Pages (11,250 words)", callback_data="15")],
        [InlineKeyboardButton("Custom Length", callback_data="custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("How long should your project be? (1 page = 750 words)\n\nSelect an option or choose 'Custom Length':", reply_markup=reply_markup)
    return PROJECT_PAGE_COUNT

async def get_project_page_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture page count selection."""
    if update.message:
        # Handle custom page count input
        try:
            page_count = int(update.message.text.strip())
            if page_count < 1:
                raise ValueError
            context.user_data['page_count'] = page_count
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number of pages.")
            return PROJECT_PAGE_COUNT
    else:
        # Handle button selection
        query = update.callback_query
        await query.answer()
        page_count = query.data
        if page_count == "custom":
            await query.edit_message_text("Please enter the exact number of pages you want (1 page = 750 words):")
            return PROJECT_PAGE_COUNT
        else:
            context.user_data['page_count'] = int(page_count)

    return confirm_project(update, context)

async def confirm_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show project summary for confirmation."""
    page_count = context.user_data.get('page_count', 5)

    # Show confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM")],
        [InlineKeyboardButton("❌ Cancel", callback_data="CANCEL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    project_summary = (
        f"📌 **Project 
