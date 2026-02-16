from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

TUTOR_QUESTION = 1

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("🧠 **Mini Tutor**\n\nAsk me any academic question.")
    return TUTOR_QUESTION

async def process_tutor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    status_msg = await update.message.reply_text("Thinking...")
    prompt = f"As an expert academic tutor, answer this question clearly and concisely: {question}"
    answer = await query_perplexica(prompt, focus_mode="academic")
    await status_msg.delete()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        TUTOR_QUESTION: [MessageHandler(filters.TEXT, process_tutor_question)],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

TUTOR_QUESTION = 1

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("🧠 **Mini Tutor**\n\nAsk me any academic question.")
    return TUTOR_QUESTION

async def process_tutor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    status_msg = await update.message.reply_text("Thinking...")
    prompt = f"As an expert academic tutor, answer this question clearly and concisely: {question}"
    answer = await query_perplexica(prompt, focus_mode="academic")
    await status_msg.delete()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        TUTOR_QUESTION: [MessageHandler(filters.TEXT, process_tutor_question)],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)
