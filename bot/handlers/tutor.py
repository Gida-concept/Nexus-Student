from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

TUTOR_QUESTION, FOLLOW_UP_QUESTION = range(2)

async def start_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for the Mini Tutor feature."""
    query = update.callback_query
    await query.answer()

    # Clear data from any previous conversation
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🧠 **Mini Tutor**\n\n"
        "Ask me any academic question! I can help with explanations, summaries, study tips, or quick answers to your coursework questions.\n\n"
        "What would you like to know?",
        reply_markup=reply_markup
    )
    return TUTOR_QUESTION

async def process_tutor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the user's question and get an AI response."""
    question = update.message.text.strip()
    
    # Remove emojis from input
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    question = emoji_pattern.sub(r'', question)
    
    if not question:
        await update.message.reply_text("❌ Please ask a valid question without emojis.")
        return TUTOR_QUESTION
        
    status_msg = await update.message.reply_text("🔮 Searching for the best answer...")
    
    try:
        prompt = f"You are an expert academic tutor. Answer this student's question clearly and concisely:\n\nQuestion: {question}\n\nProvide a detailed, well-structured answer with key points and examples where appropriate."
        answer = await query_perplexica(prompt, focus_mode="academic")
        
        # Store original question for follow-ups
        context.user_data['original_question'] = question
        
        await status_msg.delete()
        
        keyboard = [
            [InlineKeyboardButton("❓ Ask Follow-up Question", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📚 **Answer to your question**\n\n{answer}\n\nWould you like to ask a follow-up question?",
            reply_markup=reply_markup
        )
        return FOLLOW_UP_QUESTION
        
    except Exception as e:
        logger.error(f"Tutor question failed: {e}")
        await status_msg.delete()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("⚠️ Sorry, I couldn't find an answer to that question. Please try again.", reply_markup=reply_markup)
        return TUTOR_QUESTION

async def handle_followup_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle follow-up questions."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "ASK_FOLLOWUP":
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        original_question = context.user_data.get('original_question', 'your previous question')
        await query.edit_message_text(
            f"❓ What follow-up question do you have about '{original_question}'?\n\n"
            "Ask anything specific you'd like to know more about.",
            reply_markup=reply_markup
        )
        return FOLLOW_UP_QUESTION
    else:
        return ConversationHandler.END

async def process_followup_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the follow-up question and get AI response."""
    followup_question = update.message.text.strip()
    
    # Remove emojis from input
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    followup_question = emoji_pattern.sub(r'', followup_question)
    
    if not followup_question:
        await update.message.reply_text("❌ Please ask a valid follow-up question without emojis.")
        return FOLLOW_UP_QUESTION
        
    status_msg = await update.message.reply_text("🔍 Finding answer to your follow-up question...")
    
    original_question = context.user_data.get('original_question', 'the topic')
    prompt = (
        f"You are an expert academic tutor. A student asked this question: '{original_question}'\n\n"
        f"Now they're asking a follow-up: '{followup_question}'\n\n"
        f"Provide a clear, concise, and accurate answer that builds on your previous response."
    )

    try:
        answer = await query_perplexica(prompt, focus_mode="academic")
        
        keyboard = [
            [InlineKeyboardButton("❓ Ask Another Question", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_msg.delete()
        await update.message.reply_text(
            f"📚 **Follow-up Answer**\n\n{answer}\n\nWould you like to ask another follow-up question?",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Follow-up Question Error: {e}")
        await status_msg.delete()
        
        keyboard = [
            [InlineKeyboardButton("❓ Try Again", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("⚠️ Sorry, I couldn't find an answer to your question. Please try again.", reply_markup=reply_markup)
    
    return FOLLOW_UP_QUESTION

async def cancel_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the tutor conversation."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("Tutor session ended.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Tutor session ended.")
        
    return ConversationHandler.END

tutor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_tutor, pattern="^MENU_TUTOR$")],
    states={
        TUTOR_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_tutor_question)],
        FOLLOW_UP_QUESTION: [
            CallbackQueryHandler(handle_followup_question, pattern="^ASK_FOLLOWUP$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_followup_question)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_tutor)]
)
