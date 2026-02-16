from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

TUTOR_QUESTION = 1

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the Mini Tutor feature."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("🧠 **Mini Tutor**\n\nAsk me any academic question.")
    return TUTOR_QUESTION

async def process_tutor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the user's question and get an AI response."""
    question = update.message.text.strip()
    status_msg = await update.message.reply_text("Thinking...")
    
    prompt = f"As an expert academic tutor, answer this student's question clearly and concisely: {question}"
    
    try:
        answer = await query_perplexica(prompt, focus_mode="academic")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Tutor feature failed: {e}")
        await status_msg.delete()
        await update.message.reply_text("Sorry, I couldn't process your request right now.")
        
    return ConversationHandler.END

async def cancel_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the tutor conversation."""
    await update.message.reply_text("Tutor session cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        TUTOR_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_tutor_question)],
    },
    fallbacks=[CommandHandler('cancel', cancel_tutor)]
)
