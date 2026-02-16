from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

MAX_MESSAGE_LENGTH = 4096

def split_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Splits a long string into a list of smaller strings, each within the max_length.
    Tries to split at newlines or spaces to keep words intact.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    while len(text) > 0:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Find the best place to split before the max_length
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        
        # If no newline or space is found, force a split at max_length
        if split_pos == -1:
            split_pos = max_length
        
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip()
        
    return chunks

async def send_long_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    """
    Sends a long message by splitting it into multiple parts if necessary.
    The reply_markup (buttons) is only attached to the very last message.
    """
    chunks = split_text(text)
    
    for i, chunk in enumerate(chunks):
        is_last_chunk = (i == len(chunks) - 1)
        
        # Only add the keyboard to the last message
        final_reply_markup = reply_markup if is_last_chunk else None
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=chunk,
            reply_markup=final_reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
