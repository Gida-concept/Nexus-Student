from bot import db_app
from bot.models import User, PricingPlan, Subscription, Project, ProjectChapter, Assignment, CourseRequirement
from bot.models import db

def init_database():
    with db_app.app_context():
        # Create all tables
        db.create_all()
        
        # Add default monthly pricing plan (only one plan)
        if not PricingPlan.query.first():
            monthly_plan = PricingPlan(
                name="Monthly Premium",
                price=50000,  # ₦500 in kobo
                interval="monthly",
                paystack_plan_code="PLN_monthly",
                description="Access to all premium features"
            )
            db.session.add(monthly_plan)
            try:
                db.session.commit()
                print("Default monthly pricing plan added successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding default plan: {e}")
            
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
