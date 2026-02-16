from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.services.perplexica_service import query_perplexica
from bot.models import Project, ProjectChapter, User, db
from bot import app
import logging
import io

logger = logging.getLogger(__name__)

# Define states for the new project flow
TITLE, DETAILS, GENERATING = range(3)

async def start_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    
    # Store initial prompt to guide the AI later
    context.user_data['history'] = []
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text(
        "📝 **Final Year Project Generator**\n\nFirst, what is the **Project Title**?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TITLE

async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function collects all project details in one go
    if 'title' not in context.user_data:
        context.user_data['title'] = update.message.text.strip()
        await update.message.reply_text("Got it. Now, please provide the rest of the details in this format:\n\n**Department:** [Your Department]\n**Research Type:** [e.g., Survey, Experimental, System Development]\n**Number of Chapters:** [e.g., 5]\n**Referencing Style:** [e.g., APA 7th Edition]")
        return DETAILS
    
    details_text = update.message.text
    try:
        details = {}
        for line in details_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                details[key.strip().lower()] = value.strip()

        context.user_data['department'] = details.get('department', 'Not Specified')
        context.user_data['research_type'] = details.get('research type', 'Not Specified')
        context.user_data['num_chapters'] = int(details.get('number of chapters', 5))
        context.user_data['referencing'] = details.get('referencing style', 'APA 7th Edition')
        
        summary = (
            f"**Project Details Confirmation:**\n\n"
            f"**Title:** {context.user_data['title']}\n"
            f"**Department:** {context.user_data['department']}\n"
            f"**Research Type:** {context.user_data['research_type']}\n"
            f"**Chapters:** {context.user_data['num_chapters']}\n"
            f"**Style:** {context.user_data['referencing']}\n\n"
            "Is this correct?"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Start Generating", callback_data="start_generating")],
            [InlineKeyboardButton("✏️ No, Start Over", callback_data="start_over")]
        ]
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return GENERATING

    except (ValueError, KeyError) as e:
        await update.message.reply_text("There was an error in your formatting. Please provide the details again in the correct format.")
        return DETAILS

async def generate_chapters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'start_over':
        context.user_data.clear()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await query.edit_message_text("Ok, let's start over. What is the project title?", reply_markup=InlineKeyboardMarkup(keyboard))
        return TITLE

    await query.edit_message_text("Great! I will now start generating your project, chapter by chapter. This may take some time.")
    
    num_chapters = context.user_data.get('num_chapters', 5)
    
    # Construct the initial user prompt for the AI
    initial_prompt = (
        f"Project Title: {context.user_data['title']}\n"
        f"Department: {context.user_data['department']}\n"
        f"Research Type: {context.user_data['research_type']}\n"
        f"Referencing Style: {context.user_data['referencing']}\n\n"
        "Generate the first chapter (Introduction) of this project. After you are done, simply say 'Chapter 1 Complete.' and nothing else."
    )
    
    history = context.user_data.get('history', [])
    history.append({"role": "user", "content": initial_prompt})

    for i in range(1, num_chapters + 1):
        status_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✍️ Generating Chapter {i}...")
        
        try:
            ai_response = await query_perplexica("", focus_mode="project_generator", history=history)
            history.append({"role": "assistant", "content": ai_response})
            
            # Create a document in memory
            doc_content = ai_response.encode('utf-8')
            doc_stream = io.BytesIO(doc_content)
            doc_stream.name = f"Chapter_{i}.docx"
            
            await status_msg.delete()
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=doc_stream,
                caption=f"Here is Chapter {i} of your project."
            )

            # If it's not the last chapter, ask for the next one
            if i < num_chapters:
                next_prompt = f"Excellent. Now, generate Chapter {i+1} based on the previous chapters. After you are done, simply say 'Chapter {i+1} Complete.' and nothing else."
                history.append({"role": "user", "content": next_prompt})
            
        except Exception as e:
            logger.error(f"Project generation failed at Chapter {i}: {e}")
            await status_msg.delete()
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Sorry, an error occurred while generating Chapter {i}.")
            return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ All chapters have been generated!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data.clear()
    return ConversationHandler.END

async def universal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.callback_query:
        from .start import start_command
        await start_command(update, context)
    elif update.message:
        await update.message.reply_text("Session cancelled.")
    return ConversationHandler.END

project_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_project, pattern="^MENU_PROJECT$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
        DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
        GENERATING: [CallbackQueryHandler(generate_chapters)],
    },
    fallbacks=[CommandHandler('cancel', universal_cancel), CallbackQueryHandler(universal_cancel, pattern="^BACK_TO_MENU$")]
)
