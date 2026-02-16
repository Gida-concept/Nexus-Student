from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Assignment, db
from bot.services.perplexica_service import query_perplexica
from bot import app
import logging
import re

logger = logging.getLogger(__name__)

ASSIGNMENT_TOPIC, FOLLOW_UP_QUESTION = range(2)

async def start_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for assignment assistance flow."""
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(
        "📄 **Assignment Helper**\n\n"
        "Describe your assignment topic, and I'll help you with it."
    )
    return ASSIGNMENT_TOPIC

async def process_assignment_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the assignment topic."""
    topic = update.message.text.strip()
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF" u"\U00002702-\U000027B0" u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    topic = emoji_pattern.sub(r'', topic)
    if not topic:
        await update.message.reply_text("❌ Please enter a valid topic without emojis.")
        return ASSIGNMENT_TOPIC

    status_msg = await update.message.reply_text("🔍 Analyzing your assignment...")
    
    try:
        prompt = f"Analyze the following assignment topic: '{topic}'. Provide a detailed analysis, key points, and suggestions for completing the assignment. Format your response clearly with headings and bullet points."
        ai_response = await query_perplexica(prompt, focus_mode="academic")
        
        with app.app_context():
            assignment = Assignment(
                user_id=update.effective_user.id,
                topic=topic,
                ai_response=ai_response
            )
            db.session.add(assignment)
            db.session.commit()
            
        context.user_data['assignment_topic'] = topic
            
        await status_msg.delete()
        
        keyboard = [
            [InlineKeyboardButton("❓ Ask Follow-up Question", callback_data="ASK_FOLLOWUP")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ **Assignment Analysis Complete!**\n\n{ai_response[:1000]}...",
            reply_markup=reply_markup
        )
        
        return FOLLOW_UP_QUESTION
        
    except Exception as e:
        logger.error(f"Assignment processing failed: {e}")
        await status_msg.delete()
        await update.message.reply_text("⚠️ Failed to process your assignment. Please try again.")
        return ConversationHandler.END

async def cancel_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assignment help cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

assignment_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_assignment, pattern="^MENU_ASSIGNMENT$")],
    states={
        ASSIGNMENT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_assignment_topic)],
        FOLLOW_UP_QUESTION: [], # Simplified, can be expanded later
    },
    fallbacks=[CommandHandler("cancel", cancel_assignment)]
)
