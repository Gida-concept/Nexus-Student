from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging

logger = logging.getLogger(__name__)

# Define conversation states for the new tutor flow
SUBJECT, LEVEL_ASSESSMENT, ROADMAP, TEACHING, MASTERY_CHECK = range(5)

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    # Initialize the conversation history with the system prompt context
    context.user_data['history'] = []
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text(
        "🧠 **Welcome to the AI Tutor!**\n\nI can teach you any subject, from the basics to advanced topics. What subject would you like to learn today?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SUBJECT

async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subject = update.message.text.strip()
    context.user_data['subject'] = subject
    
    # First interaction with the AI to start the structured teaching
    status_msg = await update.message.reply_text("OK. Let's create a learning plan for you...")
    
    # The user's message is the first "user" turn in the conversation
    history = context.user_data.get('history', [])
    history.append({"role": "user", "content": f"I want to learn {subject}."})
    
    try:
        # The AI's first response should be the level assessment questions
        ai_response = await query_perplexica("", focus_mode="tutor", history=history)
        history.append({"role": "assistant", "content": ai_response})
        context.user_data['history'] = history
        
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text(ai_response, reply_markup=InlineKeyboardMarkup(keyboard))
        
        # The next state will handle the student's answers to the assessment
        return LEVEL_ASSESSMENT
        
    except Exception as e:
        logger.error(f"Tutor start failed: {e}")
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await status_msg.edit_text("Sorry, an error occurred. Please try again.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def process_student_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    student_response = update.message.text.strip()
    status_msg = await update.message.reply_text("Got it. Generating the next step...")

    history = context.user_data.get('history', [])
    history.append({"role": "user", "content": student_response})
    
    try:
        ai_response = await query_perplexica("", focus_mode="tutor", history=history)
        history.append({"role": "assistant", "content": ai_response})
        context.user_data['history'] = history

        await status_msg.delete()
        
        # We need a way to offer choices, but for now, we'll just show the text.
        # In a more advanced version, we'd parse the AI response for options.
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text(ai_response, reply_markup=InlineKeyboardMarkup(keyboard))

        # Stay in the teaching state to continue the conversation
        return LEVEL_ASSESSMENT
        
    except Exception as e:
        logger.error(f"Tutor conversation failed: {e}")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text("Sorry, an error occurred.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def universal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        from .start import start_command
        await start_command(update, context)
    elif update.message:
        await update.message.reply_text("Session ended.")
    return ConversationHandler.END

tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_subject)],
        LEVEL_ASSESSMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_student_response)],
        # ROADMAP, TEACHING, etc. would be handled by the same function,
        # as the AI's prompt guides the conversation flow.
    },
    fallbacks=[CommandHandler('cancel', universal_cancel), CallbackQueryHandler(universal_cancel, pattern="^BACK_TO_MENU$")]
)
