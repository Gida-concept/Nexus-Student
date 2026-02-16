from bot import app
from bot.models import User, Project, ProjectChapter, Assignment, CourseRequirement, db
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """
    Creates all database tables based on the current models.
    This script is safe to run multiple times; it will not duplicate tables.
    """
    try:
        with app.app_context():
            logger.info("Creating all database tables...")
            db.create_all()
            logger.info("✅ Database tables created successfully (or already exist).")
    except Exception as e:
        logger.error(f"❌ An error occurred during database initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Starting database initialization script...")
    init_database()
