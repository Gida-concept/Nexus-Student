from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

COURSE_NAME, FOLLOW_UP = range(2)

async def start_advisor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text(
        "🎓 **Course Advisor**\n\nPlease type the name of the course you are interested in (e.g., 'Medicine and Surgery').",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return COURSE_NAME

async def process_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course_name = update.message.text.strip()
    status_msg = await update.message.reply_text("🔎 Researching admission requirements...")
    prompt = (
        f"For a Nigerian student wanting to study '{course_name}', provide ONLY the following information concisely:\n"
        f"1. **JAMB Score:** Recommended and minimum cut-off.\n"
        f"2. **WAEC/NECO:** A list of exactly 8 compulsory subjects (including English & Maths) and 1 optional subject.\n"
        f"3. **UTME Subjects:** The 4 required subjects for JAMB."
    )
    try:
        response_text = await query_perplexica(prompt, focus_mode="webSearch")
        context.user_data['history'] = [
            {"role": "user", "content": f"Admission requirements for {course_name}"},
            {"role": "assistant", "content": response_text}
        ]
        keyboard = [
            [InlineKeyboardButton("❓ Ask a Follow-up", callback_data="ask_follow_up")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
        ]
        await status_msg.delete()
        await update.message.reply_text(
            f"📘 **Admission Guide: {course_name}**\n\n{response_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return FOLLOW_UP
    except Exception as e:
        logger.error(f"Course Advisor Error: {e}")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text("⚠️ An error occurred.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def ask_follow_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text("What is your follow-up question?", reply_markup=InlineKeyboardMarkup(keyboard))
    return FOLLOW_UP

async def process_follow_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    follow_up_question = update.message.text.strip()
    status_msg = await update.message.reply_text("Thinking...")
    history = context.user_data.get('history', [])
    history.append({"role": "user", "content": follow_up_question})
    prompt = f"Based on the previous conversation context about university admissions, answer this follow-up question:\n\nCONTEXT:\n{history}\n\nNEW QUESTION:\n{follow_up_question}"
    try:
        answer = await query_perplexica(prompt, focus_mode="academic")
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
        logger.error(f"Follow-up Error: {e}")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text("⚠️ An error occurred.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Session ended.")
    return ConversationHandler.END

advisor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_advisor, pattern="^MENU_COURSE_ADVISOR$")],
    states={
        COURSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_course_name)],
        FOLLOW_UP: [
            CallbackQueryHandler(ask_follow_up, pattern="^ask_follow_up$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_follow_up)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation), CallbackQueryHandler(cancel_conversation, pattern="^BACK_TO_MENU$")]
)
