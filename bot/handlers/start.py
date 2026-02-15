from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.models import User, db
from bot import app
from bot.config import Config

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command and the 'Back to Menu' button."""
    
    user = update.effective_user
    telegram_id = user.id
    username = user.username

    with app.app_context():
        db_user = User.query.filter_by(telegram_id=telegram_id).first()
        if not db_user:
            db_user = User(telegram_id=telegram_id, username=username)
            db.session.add(db_user)
            if telegram_id == Config.ADMIN_USER_ID:
                db_user.is_admin = True
            db.session.commit()
        
    keyboard = [
        [
            InlineKeyboardButton("🎓 Course Advisor", callback_data="MENU_COURSE_ADVISOR"),
            InlineKeyboardButton("💎 Premium / Subscribe", callback_data="MENU_SUBSCRIBE")
        ],
        [
            InlineKeyboardButton("📝 Projects", callback_data="MENU_PROJECT"),
            InlineKeyboardButton("📄 Assignments", callback_data="MENU_ASSIGNMENT")
        ],
        [
            InlineKeyboardButton("🧠 Mini Tutor", callback_data="MENU_TUTOR"),
            InlineKeyboardButton("ℹ️ Help & About", callback_data="MENU_HELP")
        ]
    ]

    if telegram_id == Config.ADMIN_USER_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="MENU_ADMIN")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"Hello, {user.first_name}! 👋\n\n"
        "I am your **Student AI Assistant**. I can help you with research, "
        "project writing, assignment solving, and course advice.\n\n"
        "Choose an option below to get started:"
    )

    # Differentiate between a /start command and a 'Back' button press
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
