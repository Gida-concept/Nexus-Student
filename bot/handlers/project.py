from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Project, ProjectChapter, db
from bot import app
from bot.services.perplexica_service import query_perplexica
from bot.utils.decorators import subscription_required
import logging
import re

logger = logging.getLogger(__name__)

PROJECT_TITLE, PROJECT_TOPIC, PROJECT_PAGE_COUNT, CONFIRM_PROJECT = range(4)
GENERATING_CHAPTER = 5

async def start_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for project creation flow."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 **Create New Project**\n\n"
        "Let's create a new academic project. I'll guide you through the process.\n\n"
        "First, please enter the title of your project:",
        reply_markup=reply_markup
    )
    return PROJECT_TITLE

async def get_project_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture project title."""
    project_title = update.message.text.strip()
    
    # Remove emojis from input
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    project_title = emoji_pattern.sub(r'', project_title)
    
    if not project_title:
        await update.message.reply_text("❌ Please enter a valid project title without emojis.")
        return PROJECT_TITLE
        
    context.user_data['project_title'] = project_title
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Great! Now, please describe the topic of your project in detail:",
        reply_markup=reply_markup
    )
    return PROJECT_TOPIC

async def get_project_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture project topic."""
    project_topic = update.message.text.strip()
    
    # Remove emojis from input
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    project_topic = emoji_pattern.sub(r'', project_topic)
    
    if not project_topic:
        await update.message.reply_text("❌ Please enter a valid project topic without emojis.")
        return PROJECT_TOPIC
        
    context.user_data['project_topic'] = project_topic

    # Show page count options
    keyboard = [
        [InlineKeyboardButton("5 Pages (3,750 words)", callback_data="5")],
        [InlineKeyboardButton("10 Pages (7,500 words)", callback_data="10")],
        [InlineKeyboardButton("15 Pages (11,250 words)", callback_data="15")],
        [InlineKeyboardButton("Custom Length", callback_data="custom")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "How long should your project be? (1 page = 750 words)\n\n"
        "Select an option or choose 'Custom Length':",
        reply_markup=reply_markup
    )
    return PROJECT_PAGE_COUNT

async def get_project_page_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture page count selection."""
    if update.message:
        # Handle custom page count input
        try:
            page_count = int(update.message.text.strip())
            if page_count < 1:
                raise ValueError
            context.user_data['page_count'] = page_count
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number of pages.")
            return PROJECT_PAGE_COUNT
    else:
        # Handle button selection
        query = update.callback_query
        await query.answer()
        page_count = query.data
        if page_count == "custom":
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Please enter the exact number of pages you want (1 page = 750 words):", reply_markup=reply_markup)
            return PROJECT_PAGE_COUNT
        else:
            context.user_data['page_count'] = int(page_count)

    return await confirm_project(update, context)

async def confirm_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show project summary for confirmation."""
    page_count = context.user_data.get('page_count', 5)

    # Show confirmation
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="CONFIRM")],
        [InlineKeyboardButton("❌ Cancel", callback_data="CANCEL")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    project_summary = (
        f"📌 **Project Summary**\n\n"
        f"Title: {context.user_data.get('project_title', 'Not specified')}\n"
        f"Topic: {context.user_data.get('project_topic', 'Not specified')}\n"
        f"Length: {page_count} pages ({page_count * 750} words)\n\n"
        "Is this correct?"
    )

    if update.message:
        await update.message.reply_text(project_summary, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(project_summary, reply_markup=reply_markup)

    return CONFIRM_PROJECT

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create the project in the database."""
    query = update.callback_query
    await query.answer()

    if query.data == "CANCEL":
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Project creation cancelled.", reply_markup=reply_markup)
        return ConversationHandler.END

    # Create project record
    with app.app_context():
        project = Project(
            user_id=update.effective_user.id,
            title=context.user_data['project_title'],
            topic=context.user_data['project_topic'],
            page_count=context.user_data['page_count'],
            word_count=context.user_data['page_count'] * 750
        )
        db.session.add(project)
        db.session.commit()

        # Store project ID in context
        context.user_data['project_id'] = project.id

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ Project created successfully!\n\n"
        "Now let's generate the first chapter. What should the chapter be about?",
        reply_markup=reply_markup
    )
    return GENERATING_CHAPTER

async def generate_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a chapter using the new search pipeline."""
    chapter_title = update.message.text.strip()
    
    # Remove emojis from input
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    chapter_title = emoji_pattern.sub(r'', chapter_title)
    
    if not chapter_title:
        await update.message.reply_text("❌ Please enter a valid chapter title without emojis.")
        return GENERATING_CHAPTER
        
    project_id = context.user_data.get('project_id')

    if not project_id:
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ Project session expired. Please start over.", reply_markup=reply_markup)
        return ConversationHandler.END

    # Show "generating" status
    status_msg = await update.message.reply_text("🔮 Generating chapter content with academic research...")

    # Build prompt for AI
    prompt = (
        f"Generate a detailed academic chapter for a project titled '{context.user_data['project_title']}'. "
        f"The chapter should be titled '{chapter_title}' and cover the following topic: "
        f"'{context.user_data['project_topic']}'. "
        f"Write in a formal academic style with proper citations where necessary. "
        f"Maintain a length appropriate for a {context.user_data['page_count']}-page project. "
        f"Use the following academic sources for reference:"
    )

    try:
        # Query the new search pipeline
        chapter_content = await query_perplexica(prompt, focus_mode="academic")

        # Save to database
        with app.app_context():
            chapter = ProjectChapter(
                project_id=project_id,
                title=chapter_title,
                content=chapter_content
            )
            db.session.add(chapter)
            db.session.commit()

        # Show success
        await status_msg.delete()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Chapter '{chapter_title}' generated successfully!\n\n"
            f"Here's a preview of the first 500 characters:\n\n"
            f"{chapter_content[:500]}...\n\n"
            f"Would you like to generate another chapter?",
            reply_markup=reply_markup
        )

        # Reset for next chapter
        context.user_data['project_id'] = project_id
        return GENERATING_CHAPTER

    except Exception as e:
        logger.error(f"Chapter generation failed: {e}")
        await status_msg.delete()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("⚠️ Failed to generate chapter. Please try again.", reply_markup=reply_markup)
        return ConversationHandler.END

async def cancel_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the project creation flow."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("Project creation cancelled.", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Project creation cancelled.")

    context.user_data.clear()
    return ConversationHandler.END

project_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_project, pattern="^MENU_PROJECT$")],
    states={
        PROJECT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_project_title)],
        PROJECT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_project_topic)],
        PROJECT_PAGE_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_project_page_count),
            CallbackQueryHandler(get_project_page_count, pattern="^[0-9]+$|custom")
        ],
        CONFIRM_PROJECT: [
            CallbackQueryHandler(create_project, pattern="^CONFIRM$"),
            CallbackQueryHandler(cancel_project, pattern="^CANCEL$")
        ],
        GENERATING_CHAPTER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, generate_chapter),
            CommandHandler("cancel", cancel_project)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_project)]
)
