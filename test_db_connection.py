from bot import db_app
from bot.models import db

def test_connection():
    try:
        with db_app.app_context():
            # Try to connect to the database
            db.engine.connect()
            print("✅ Successfully connected to Supabase database!")
            
            # Test by getting table names
            from sqlalchemy import text
            result = db.engine.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = [row[0] for row in result]
            print(f"Existing tables: {tables}")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    test_connection()
