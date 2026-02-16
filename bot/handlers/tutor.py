from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging

logger = logging.getLogger(__name__)

TUTOR_QUESTION, FOLLOW_UP = range(2)

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text(
        "🧠 **Mini Tutor**\n\nAsk me any academic question. I will provide a detailed explanation.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TUTOR_QUESTION

async def process_tutor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    status_msg = await update.message.reply_text("🤔 Thinking...")
    prompt = f"As an expert academic tutor, answer this student's question clearly and concisely: {question}"
    
    try:
        answer = await query_perplexica(prompt, focus_mode="academic")
        context.user_data['history'] = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ]
        
        await status_msg.delete()
        keyboard = [
            [InlineKeyboardButton("❓ Ask a Follow-up", callback_data="ask_follow_up")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
        ]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
        return FOLLOW_UP

    except Exception as e:
        logger.error(f"Tutor failed: {e}")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text("Sorry, an error occurred.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def ask_follow_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text("What is your follow-up question?", reply_markup=InlineKeyboardMarkup(keyboard))
    return FOLLOW_UP

async def process_follow_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    follow_up_question = update.message.text.strip()
    status_msg = await update.message.reply_text("Thinking about your follow-up...")
    
    history = context.user_data.get('history', [])
    history.append({"role": "user", "content": follow_up_question})
    
    # Construct a prompt that includes the history
    prompt_with_history = "Continue the conversation based on the history provided.\n\n"
    for message in history:
        prompt_with_history += f"{message['role'].title()}: {message['content']}\n"
    prompt_with_history += "Assistant:"

    try:
        answer = await query_perplexica(prompt_with_history, focus_mode="academic")
        history.append({"role": "assistant", "content": answer})
        context.user_data['history'] = history

        await status_msg.delete()
        keyboard = [
            [InlineKeyboardButton("❓ Ask Another Follow-up", callback_data="ask_follow_up")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
        ]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
        return FOLLOW_UP

    except Exception as e:
        logger.error(f"Tutor follow-up failed: {e}")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text("Sorry, an error occurred.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def universal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        from .start import start_command # Local import to avoid circular dependency
        await start_command(update, context)
    elif update.message:
        await update.message.reply_text("Session cancelled.")
    return ConversationHandler.END

tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        TUTOR_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_tutor_question)],
        FOLLOW_UP: [
            CallbackQueryHandler(ask_follow_up, pattern="^ask_follow_up$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_follow_up)
        ],
    },
    fallbacks=[CommandHandler('cancel', universal_cancel), CallbackQueryHandler(universal_cancel, pattern="^BACK_TO_MENU$")]
)
