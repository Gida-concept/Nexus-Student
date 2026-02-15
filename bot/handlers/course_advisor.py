from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

COURSE_NAME, FOLLOW_UP_QUESTION = range(2)

async def advisor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point when the user clicks the 'Course Advisor' button."""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎓 **Course Advisor**\n\n"
        "I can help you with admission requirements for any course in Nigerian universities.\n\n"
        "Please type the name of the course you want to study:",
        reply_markup=reply_markup
    )
    return COURSE_NAME

async def process_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's text input and queries the AI."""
    course_name = update.message.text.strip()
    
    # Remove emojis from input
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    course_name = emoji_pattern.sub(r'', course_name)
    
    if not course_name:
        await update.message.reply_text("❌ Please enter a valid course name without emojis.")
        return COURSE_NAME
        
    status_message = await update.message.reply_text("🔎 Researching admission requirements...")
    
    # Updated prompt to be more direct and specific about Nigerian standards
    prompt = (
        f"You are an expert on Nigerian University Admission. A student wants to study '{course_name}'. "
        f"Provide ONLY the following information in a clear, concise format with no long explanations:\n\n"
        f"1. JAMB Score: State only the recommended score and minimum cut-off mark as numbers.\n"
        f"2. WAEC/NECO Requirements: List EXACTLY 8 compulsory subjects (MUST include English Language and Mathematics) plus 1 optional subject. Format as: 'Compulsory: [subject1], [subject2], ... | Optional: [subject]'\n"
        f"3. UTME Subjects: List EXACTLY 4 subjects required for JAMB.\n\n"
        f"Format your response exactly like this example:\n"
        f"JAMB Score: Recommended: 250, Minimum: 200\n"
        f"WAEC/NECO: Compulsory: English Language, Mathematics, Physics, Chemistry, Biology, Economics, Geography, Government | Optional: Further Mathematics\n"
        f"UTME Subjects: English Language, Mathematics, Physics, Chemistry"
    )

    try:
        response_text = await query_perplexica(prompt, focus_mode="webSearch")
        
        # Store course name for follow-up questions
        context.user_data['current_course'] = course_name
        
        # Add back button to response
        keyboard = [
            [InlineKeyboardButton("❓ Ask Follow-up Question", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_message.delete()
        await update.message.reply_text(
            f"📘 **Admission Guide: {course_name}**\n\n{response_text}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Course Advisor Error: {e}")
        await status_message.delete()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("⚠️ Sorry, I couldn't retrieve the details at this time.", reply_markup=reply_markup)
        return ConversationHandler.END
    
    return FOLLOW_UP_QUESTION

async def handle_followup_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle follow-up questions about the current course."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "ASK_FOLLOWUP":
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"❓ What follow-up question do you have about {context.user_data.get('current_course', 'this course')}?\n\n"
            "Ask anything specific about admission requirements, career prospects, or related information.",
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
        
    status_message = await update.message.reply_text("🔍 Finding answer to your follow-up question...")
    
    course_name = context.user_data.get('current_course', 'the course')
    prompt = (
        f"You are an expert on Nigerian University Admission. A student is asking a follow-up question about studying '{course_name}'.\n\n"
        f"Question: {followup_question}\n\n"
        f"Provide a clear, concise, and accurate answer based on Nigerian educational standards. Keep it brief and to the point."
    )

    try:
        response_text = await query_perplexica(prompt, focus_mode="academic")
        
        keyboard = [
            [InlineKeyboardButton("❓ Ask Another Question", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_message.delete()
        await update.message.reply_text(
            f"📚 **Follow-up Answer**\n\n{response_text}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Follow-up Question Error: {e}")
        await status_message.delete()
        
        keyboard = [
            [InlineKeyboardButton("❓ Try Again", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("⚠️ Sorry, I couldn't find an answer to your question. Please try again.", reply_markup=reply_markup)
    
    return FOLLOW_UP_QUESTION

async def cancel_advisor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /cancel command during the conversation."""
    await update.message.reply_text("👋 Course advisor cancelled.")
    return ConversationHandler.END

advisor_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(advisor_start, pattern="^MENU_COURSE_ADVISOR$")],
    states={
        COURSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_course_name)],
        FOLLOW_UP_QUESTION: [
            CallbackQueryHandler(handle_followup_question, pattern="^ASK_FOLLOWUP$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, process_followup_question)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_advisor)]
)
