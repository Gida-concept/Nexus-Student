from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Assignment, db
from bot.services.file_service import process_uploaded_pdf
from bot.services.perplexica_service import query_perplexica
from bot import app
import os
import logging

logger = logging.getLogger(__name__)

ASSIGNMENT_TOPIC, ASSIGNMENT_FILE, PROCESSING_ASSIGNMENT = range(3)

async def start_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for assignment assistance flow."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📄 **Assignment Helper**\n\nI can help you with your assignments! Please describe the assignment topic:")
    return ASSIGNMENT_TOPIC

async def get_assignment_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture assignment topic."""
    context.user_data['assignment_topic'] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("📁 Upload PDF", callback_data="UPLOAD_PDF")],
        [InlineKeyboardButton("✏️ Continue Without File", callback_data="NO_FILE")],
        [InlineKeyboardButton("❌ Cancel", callback_data="CANCEL")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Would you like to upload a PDF reference for your assignment?", reply_markup=reply_markup)
    return ASSIGNMENT_FILE

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PDF file upload."""
    query = update.callback_query
    await query.answer()
    if query.data == "CANCEL":
        await query.edit_message_text("Assignment process cancelled.")
        return ConversationHandler.END
    if query.data == "NO_FILE":
        await query.edit_message_text("Understood. I'll proceed without a PDF reference.\n\nPlease wait while I analyze your assignment topic...")
        return process_assignment(update, context)
    await query.edit_message_text("Please upload your PDF file now. You can send it as a document in this chat.")
    return ASSIGNMENT_FILE

async def process_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the assignment with or without PDF."""
    if update.message and update.message.document:
        file = await update.message.document.get_file()
        file_path = f"/tmp/{file.file_id}.pdf"
        await file.download_to_drive(file_path)
        file_url, extracted_text = process_uploaded_pdf(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        if not file_url or not extracted_text:
            await update.message.reply_text("⚠️ Failed to process the PDF. Please try again.")
            return ConversationHandler.END
        context.user_data['file_url'] = file_url
        context.user_data['extracted_text'] = extracted_text
    status_msg = await update.message.reply_text("🔍 Analyzing your assignment...")
    try:
        topic = context.user_data.get('assignment_topic', 'your assignment')
        reference_text = context.user_data.get('extracted_text', '')
        prompt = f"Analyze the following assignment topic: '{topic}'. Use this reference material if provided:\n\n{reference_text}\n\nProvide a detailed analysis, key points, and suggestions for completing the assignment. Format your response clearly with headings and bullet points."
        ai_response = await query_perplexica(prompt, focus_mode="academic")
        with app.app_context():
            assignment = Assignment(
                user_id=update.effective_user.id,
                topic=topic,
                file_url=context.user_data.get('file_url'),
                extracted_text=reference_text,
                ai_response=ai_response
            )
            db.session.add(assignment)
            db.session.commit()
        await status_msg.delete()
        await update.message.reply_text(f"✅ Assignment Analysis Complete!\n\nHere's a summary of my analysis:\n\n{ai_response[:1000]}...\n\nWould you like to see the full analysis or start a new assignment?")
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Assignment processing failed: {e}")
        await status_msg.delete()
        await update.message.reply_text("⚠️ Failed to process your assignment. Please try again.")
        return ConversationHandler.END

async def cancel_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the assignment flow."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Assignment process cancelled.")
    else:
        await update.message.reply_text("Assignment process cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

assignment_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_assignment, pattern="^MENU_ASSIGNMENT$")],
    states={
        ASSIGNMENT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_assignment_topic)],
        ASSIGNMENT_FILE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_file_upload),
            CallbackQueryHandler(handle_file_upload, pattern="^(UPLOAD_PDF|NO_FILE|CANCEL)$"),
            MessageHandler(filters.Document.ALL, process_assignment)
        ],
        PROCESSING_ASSIGNMENT: [MessageHandler(filters.ALL, process_assignment)]
    },
    fallbacks=[CommandHandler("cancel", cancel_assignment)]
)
