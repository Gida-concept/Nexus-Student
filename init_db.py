from bot import db_app
from bot.models import User, PricingPlan, Subscription, Project, ProjectChapter, Assignment, CourseRequirement

def init_database():
    with db_app.app_context():
        # Create all tables
        db_app.create_all()
        
        # Add some default pricing plans (optional)
        if not PricingPlan.query.first():
            monthly_plan = PricingPlan(
                name="Monthly Premium",
                price=50000,  # ₦500 in kobo
                interval="monthly",
                paystack_plan_code="PLN_monthly",
                description="Access to all premium features"
            )
            yearly_plan = PricingPlan(
                name="Yearly Premium",
                price=500000,  # ₦5000 in kobo
                interval="yearly",
                paystack_plan_code="PLN_yearly",
                description="Access to all premium features"
            )
            db_app.session.add(monthly_plan)
            db_app.session.add(yearly_plan)
            db_app.session.commit()
            
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
