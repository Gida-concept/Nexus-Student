import os
import fitz  # PyMuPDF
import cloudinary
import cloudinary.uploader
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

# Configure Cloudinary
if Config.CLOUDINARY_URL:
    # If using the environment variable format cloudinary://key:secret@cloudname
    cloudinary.config(cloudinary_url=Config.CLOUDINARY_URL)


def process_uploaded_pdf(file_path: str) -> tuple:
    """
    Downloads a PDF from Telegram (assumed file is already downloaded locally via bot),
    uploads it to Cloudinary, and extracts text.

    Args:
        file_path (str): The local path where the PDF was downloaded by the bot.

    Returns:
        tuple: (file_url, extracted_text) or (None, None) if failed.
    """

    try:
        # 1. Upload Original File to Cloudinary
        # We use 'resource_type=auto' to ensure it's handled correctly
        upload_result = cloudinary.uploader.upload(
            file_path,
            resource_type="raw",
            folder="student_ai_documents"
        )
        file_url = upload_result.get("secure_url")

        # 2. Extract Text using PyMuPDF
        extracted_text = ""
        doc = fitz.open(file_path)
        for page in doc:
            extracted_text += page.get_text()
        doc.close()

        return file_url, extracted_text

    except Exception as e:
        logger.error(f"File Service Error: {str(e)}")
        return None, None


def clean_temp_file(file_path: str):
    """Removes a file from the filesystem."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting temp file {file_path}: {e}")