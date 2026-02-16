from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Assignment, db
from bot.services.perplexica_service import query_perplexica
from bot import app
import logging
import re

logger = logging.getLogger(__name__)

ASSIGNMENT_TOPIC = 1

async def start_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("📄 **Assignment Helper**\n\nDescribe your assignment topic.")
    return ASSIGNMENT_TOPIC

async def process_assignment_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.strip()
    status_msg = await update.message.reply_text("Analyzing...")
    prompt = f"Analyze the assignment topic '{topic}' and provide a detailed analysis, key points, and suggestions."
    ai_response = await query_perplexica(prompt, focus_mode="academic")
    with app.app_context():
        assignment = Assignment(user_id=update.effective_user.id, topic=topic, ai_response=ai_response)
        db.session.add(assignment)
        db.session.commit()
    await status_msg.delete()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await update.message.reply_text(f"**Analysis for '{topic}':**\n\n{ai_response}", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return ConversationHandler.END

assignment_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_assignment, pattern="^MENU_ASSIGNMENT$")],
    states={
        ASSIGNMENT_TOPIC: [MessageHandler(filters.TEXT, process_assignment_topic)],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)
