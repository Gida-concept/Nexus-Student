from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging

logger = logging.getLogger(__name__)

TUTOR_QUESTION = 1

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the Mini Tutor feature."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🧠 **Mini Tutor**\n\nAsk me any academic question! I can help with explanations, summaries, study tips, or quick answers to your coursework questions.\n\nWhat would you like to know?")
    return TUTOR_QUESTION

async def process_tutor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the user's question and get an AI response."""
    question = update.message.text.strip()
    if not question:
        await update.message.reply_text("❌ Please ask a valid question.")
        return TUTOR_QUESTION
    status_msg = await update.message.reply_text("🔮 Searching for the best answer...")
    try:
        prompt = f"You are an expert academic tutor. Answer this student's question clearly and concisely:\n\nQuestion: {question}\n\nProvide a detailed, well-structured answer with key points and examples where appropriate."
        answer = await query_perplexica(prompt, focus_mode="academic")
        await status_msg.delete()
        await update.message.reply_text(f"📚 **Answer to your question**\n\n{answer}\n\nWould you like to ask another question?")
        return TUTOR_QUESTION
    except Exception as e:
        logger.error(f"Tutor question failed: {e}")
        await status_msg.delete()
        await update.message.reply_text("⚠️ Sorry, I couldn't find an answer to that question. Please try again.")
        return TUTOR_QUESTION

async def cancel_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the tutor conversation."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Tutor session ended.")
    else:
        await update.message.reply_text("Tutor session ended.")
    return ConversationHandler.END

# Define the Conversation Handler (removed per_* settings)
tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        TUTOR_QUESTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_tutor_question),
            CommandHandler("cancel", cancel_tutor)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_tutor)]
)
