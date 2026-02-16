from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Assignment, User, db
from bot import app
from bot.services.perplexica_service import query_perplexica
import logging

logger = logging.getLogger(__name__)

ASSIGNMENT_TOPIC, FOLLOW_UP = range(2)

async def start_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text("📄 **Assignment Helper**\n\nDescribe your assignment topic.", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASSIGNMENT_TOPIC

async def process_assignment_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.strip()
    status_msg = await update.message.reply_text("Analyzing...")
    prompt = f"Analyze the assignment topic '{topic}' and provide a detailed analysis, key points, and suggestions."
    try:
        ai_response = await query_perplexica(prompt, focus_mode="academic")
        with app.app_context():
            user = User.query.filter_by(telegram_id=update.effective_user.id).first()
            if not user:
                await update.message.reply_text("Please /start the bot first.")
                return ConversationHandler.END
            assignment = Assignment(user_id=user.id, topic=topic, ai_response=ai_response)
            db.session.add(assignment)
            db.session.commit()
        context.user_data['history'] = [{"role": "user", "content": f"Topic: {topic}"}, {"role": "assistant", "content": ai_response}]
        await status_msg.delete()
        keyboard = [
            [InlineKeyboardButton("❓ Ask a Follow-up", callback_data="ask_follow_up")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
        ]
        await update.message.reply_text(
            f"**Analysis for '{topic}':**\n\n{ai_response[:1000]}...",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown'
        )
        return FOLLOW_UP
    except Exception as e:
        logger.error(f"Assignment failed: {e}")
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
    prompt = f"Based on the previous analysis, answer this new question:\n\nCONTEXT:\n{history}\n\nNEW QUESTION:\n{follow_up_question}"
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

async def universal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        from .start import start_command
        await start_command(update, context)
    elif update.message:
        await update.message.reply_text("Session cancelled.")
    return ConversationHandler.END

assignment_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_assignment, pattern="^MENU_ASSIGNMENT$")],
    states={
        ASSIGNMENT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_assignment_topic)],
        FOLLOW_UP: [
            CallbackQueryHandler(ask_follow_up, pattern="^ask_follow_up$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_follow_up)
        ],
    },
    fallbacks=[CommandHandler('cancel', universal_cancel), CallbackQueryHandler(universal_cancel, pattern="^BACK_TO_MENU$")]
)
