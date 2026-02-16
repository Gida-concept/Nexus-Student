from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Project, ProjectChapter, User, db
from bot import app
from bot.services.perplexica_service import query_perplexica
import logging

logger = logging.getLogger(__name__)

PROJECT_TITLE, PROJECT_TOPIC, PROJECT_PAGE_COUNT, CONFIRM_PROJECT, GENERATING_CHAPTER, FOLLOW_UP = range(6)

async def start_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text(
        "📝 **New Project**\n\nFirst, what is the title of your project?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PROJECT_TITLE

async def get_project_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['project_title'] = update.message.text.strip()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await update.message.reply_text("Great. Now, describe the main topic.", reply_markup=InlineKeyboardMarkup(keyboard))
    return PROJECT_TOPIC

async def get_project_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['project_topic'] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("5 Pages", callback_data="5"), InlineKeyboardButton("10 Pages", callback_data="10")],
        [InlineKeyboardButton("15 Pages", callback_data="15"), InlineKeyboardButton("Custom", callback_data="custom")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
    ]
    await update.message.reply_text("How long should each chapter be?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PROJECT_PAGE_COUNT

async def get_project_page_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        try:
            context.user_data['page_count'] = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
            return PROJECT_PAGE_COUNT
    else:
        query = update.callback_query
        await query.answer()
        if query.data == "custom":
            await query.edit_message_text("Please enter the number of pages:")
            return PROJECT_PAGE_COUNT
        context.user_data['page_count'] = int(query.data)
    return await confirm_project(update, context)

async def confirm_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page_count = context.user_data.get('page_count', 5)
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Create", callback_data="confirm")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
    ]
    summary = f"**Project Summary:**\nTitle: {context.user_data.get('project_title')}\nTopic: {context.user_data.get('project_topic')}\nPages per Chapter: {page_count}"
    if update.message:
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return CONFIRM_PROJECT

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    with app.app_context():
        user = User.query.filter_by(telegram_id=update.effective_user.id).first()
        project = Project(user_id=user.id, title=context.user_data['project_title'], topic=context.user_data['project_topic'], page_count=context.user_data['page_count'], word_count=context.user_data['page_count'] * 750)
        db.session.add(project)
        db.session.commit()
        context.user_data['project_id'] = project.id
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text("Project created! What is the title of your first chapter?", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENERATING_CHAPTER

async def generate_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter_title = update.message.text.strip()
    status_msg = await update.message.reply_text("🔎 Researching and writing...")
    prompt = f"Generate an academic chapter titled '{chapter_title}' for a project on '{context.user_data['project_topic']}'..."
    try:
        chapter_content = await query_perplexica(prompt, focus_mode="academic")
        with app.app_context():
            project_id = context.user_data['project_id']
            chapter = ProjectChapter(project_id=project_id, title=chapter_title, content=chapter_content)
            db.session.add(chapter)
            db.session.commit()
        context.user_data['history'] = [{"role": "user", "content": f"Chapter on {chapter_title}"}, {"role": "assistant", "content": chapter_content}]
        await status_msg.delete()
        keyboard = [
            [InlineKeyboardButton("❓ Ask a Follow-up", callback_data="ask_follow_up")],
            [InlineKeyboardButton("➕ Generate Next Chapter", callback_data="next_chapter")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]
        ]
        await update.message.reply_text(f"**{chapter_title}**\n\n{chapter_content[:1000]}...", reply_markup=InlineKeyboardMarkup(keyboard))
        return FOLLOW_UP
    except Exception as e:
        logger.error(f"Chapter generation failed: {e}")
        await status_msg.delete()
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
        await update.message.reply_text("⚠️ An error occurred.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

async def ask_next_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await query.edit_message_text("What is the title of the next chapter?", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENERATING_CHAPTER

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
        PROJECT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_project_title)],
        PROJECT_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_project_topic)],
        PROJECT_PAGE_COUNT: [CallbackQueryHandler(get_project_page_count), MessageHandler(filters.TEXT & ~filters.COMMAND, get_project_page_count)],
        CONFIRM_PROJECT: [CallbackQueryHandler(create_project, pattern="^confirm$")],
        GENERATING_CHAPTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_chapter)],
        FOLLOW_UP: [CallbackQueryHandler(ask_next_chapter, pattern="^next_chapter$")],
    },
    fallbacks=[CommandHandler('cancel', universal_cancel), CallbackQueryHandler(universal_cancel, pattern="^BACK_TO_MENU$")]
)
