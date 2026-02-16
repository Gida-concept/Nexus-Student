from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from bot.models import Project, ProjectChapter, db
from bot import app
from bot.services.perplexica_service import query_perplexica
import logging
import re

logger = logging.getLogger(__name__)

PROJECT_TITLE, PROJECT_TOPIC, PROJECT_PAGE_COUNT, CONFIRM_PROJECT, GENERATING_CHAPTER = range(5)

async def start_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("📝 **New Project**\n\nFirst, what is the title of your project?")
    return PROJECT_TITLE

async def get_project_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['project_title'] = update.message.text.strip()
    await update.message.reply_text("Great. Now, describe the main topic of your project.")
    return PROJECT_TOPIC

async def get_project_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['project_topic'] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("5 Pages", callback_data="5"), InlineKeyboardButton("10 Pages", callback_data="10")],
        [InlineKeyboardButton("15 Pages", callback_data="15"), InlineKeyboardButton("Custom", callback_data="custom")]
    ]
    await update.message.reply_text("How long should each chapter be?", reply_markup=InlineKeyboardMarkup(keyboard))
    return PROJECT_PAGE_COUNT

async def get_project_page_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page_count = query.data
    if page_count == "custom":
        await query.edit_message_text("Please enter the number of pages:")
        return PROJECT_PAGE_COUNT
    context.user_data['page_count'] = int(page_count)
    return await confirm_project(update, context)

async def confirm_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page_count = context.user_data.get('page_count', 5)
    keyboard = [[InlineKeyboardButton("✅ Confirm & Create", callback_data="confirm")]]
    summary = (
        f"**Project Summary:**\n"
        f"Title: {context.user_data.get('project_title')}\n"
        f"Topic: {context.user_data.get('project_topic')}\n"
        f"Pages per Chapter: {page_count}"
    )
    if update.message:
        await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(summary, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return CONFIRM_PROJECT

async def create_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
        context.user_data['project_id'] = project.id
    await query.edit_message_text("Project created! What is the title of your first chapter?")
    return GENERATING_CHAPTER

async def generate_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter_title = update.message.text.strip()
    status_msg = await update.message.reply_text(" researching and writing...")
    prompt = f"Generate an academic chapter titled '{chapter_title}' for a project on '{context.user_data['project_topic']}'..."
    chapter_content = await query_perplexica(prompt, focus_mode="academic")
    with app.app_context():
        project_id = context.user_data['project_id']
        chapter = ProjectChapter(project_id=project_id, title=chapter_title, content=chapter_content)
        db.session.add(chapter)
        db.session.commit()
    await status_msg.delete()
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="BACK_TO_MENU")]]
    await update.message.reply_text(f"**{chapter_title}**\n\n{chapter_content[:1000]}...", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

project_conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_project, pattern="^MENU_PROJECT$")],
    states={
        PROJECT_TITLE: [MessageHandler(filters.TEXT, get_project_title)],
        PROJECT_TOPIC: [MessageHandler(filters.TEXT, get_project_topic)],
        PROJECT_PAGE_COUNT: [CallbackQueryHandler(get_project_page_count)],
        CONFIRM_PROJECT: [CallbackQueryHandler(create_project)],
        GENERATING_CHAPTER: [MessageHandler(filters.TEXT, generate_chapter)],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)
