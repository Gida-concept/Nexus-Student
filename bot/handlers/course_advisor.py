from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler
from bot.services.perplexica_service import query_perplexica
import logging

logger = logging.getLogger(__name__)

# Conversation States
COURSE_NAME = 1

async def advisor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point when the user clicks the 'Course Advisor' button."""
    query = update.callback_query
    await query.answer()
    
    # Clear previous context
    context.user_data.clear()
    
    # Prompt user for course input via chat
    await query.edit_message_text(
        "🎓 **Course Advisor**\n\n"
        "I can help you with admission requirements for any course in Nigerian universities.\n\n"
        "Please type the name of the course you want to study:"
    )
    return COURSE_NAME

async def process_course_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the user's text input and queries Perplexica for Nigerian admission requirements."""
    course_name = update.message.text.strip()
    
    # Show a "thinking" status
    status_message = await update.message.reply_text("🔎 Researching admission requirements via Perplexica...")
    
    # Construct a strict prompt for the AI to ensure we get the specific Nigerian format
    prompt = (
        f"You are an expert on Nigerian University Admission. A student wants to study '{course_name}'. "
        f"Based on the Nigerian standard, provide the following details clearly:\n\n"
        f"1. **JAMB Score:** The recommended JAMB score and the minimum cut-off mark.\n"
        f"2. **WAEC/NECO Requirements:** List exactly 8 minimum compulsory subjects (Must include English and Mathematics) required for this course, plus 1 optional subject.\n"
        f"3. **UTME Subjects:** The exact 4 subjects the student must sit for in JAMB for this course.\n\n"
        f"Use bullet points and emojis for readability."
    )

    try:
        # Query Perplexica
        response_text = await query_perplexica(prompt, focus_mode="webSearch")
        
        # Clean up the thinking message and send the final result
        await status_message.delete()
        await update.message.reply_text(
            f"📘 **Admission Guide: {course_name}**\n\n"
            f"{response_text}"
        )
        
    except Exception as e:
        logger.error(f"Course Advisor Error: {e}")
        await status_message.delete()
        await update.message.reply_text("⚠️ Sorry, I couldn't retrieve the details at this time. Please try again later.")

    return ConversationHandler.END

async def cancel_advisor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /cancel command during the conversation."""
    await update.message.reply_text("👋 Course advisor cancelled.")
    return ConversationHandler.END

# Define the Conversation Handler
advisor_conversation_handler = ConversationHandler(
    entry_points=[], # Triggered via callback query in router
    states={
        COURSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_course_name)],
    },
    fallbacks=[CommandHandler("cancel", cancel_advisor)]
)
