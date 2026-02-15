from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a help message when the 'Help & About' button is pressed."""
    query = update.callback_query
    await query.answer()

    help_text = (
        "**Nexus Student AI Bot Help**\n\n"
        "Here are the available features:\n\n"
        "🎓 **Course Advisor**: Get admission requirements for Nigerian universities.\n\n"
        "📝 **Projects**: Start a new research project and generate chapters.\n\n"
        "📄 **Assignments**: Get help with your assignments, with or without a PDF.\n\n"
        "🧠 **Mini Tutor**: Ask any academic question and get a detailed explanation.\n\n"
        "💎 **Subscribe**: View and subscribe to premium plans to unlock all features.\n\n"
        "Use the buttons below or the corresponding commands to get started."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="BACK_TO_MENU")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=help_text, reply_markup=reply_markup, parse_mode='Markdown')
