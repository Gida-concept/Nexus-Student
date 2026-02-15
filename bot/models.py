from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    projects = db.relationship('Project', backref='user', lazy=True, cascade="all, delete-orphan")
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, order_by="desc(Subscription.created_at)")
    assignments = db.relationship('Assignment', backref='user', lazy=True)

    @property
    def is_premium(self):
        """Helper to check if user has an active subscription."""
        # Check for any active subscription
        active_sub = Subscription.query.filter_by(
            user_id=self.id,
            status='active'
        ).first()
        return bool(active_sub)


class PricingPlan(db.Model):
    __tablename__ = 'pricing_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Monthly Premium"
    price = db.Column(db.Integer, nullable=False)  # Amount in Kobo (NGN * 100)
    interval = db.Column(db.String(20), nullable=False)  # 'monthly' or 'yearly'
    paystack_plan_code = db.Column(db.String(100), unique=True, nullable=False)  # Code from Paystack
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('pricing_plans.id'), nullable=False)

    # Paystack Details
    paystack_subscription_code = db.Column(db.String(100), unique=True, nullable=True)
    paystack_customer_code = db.Column(db.String(100), nullable=True)
    paystack_email = db.Column(db.String(100), nullable=True)

    status = db.Column(db.String(20), default='inactive')  # active, cancelled, expired
    next_payment_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.Text, nullable=False)
    page_count = db.Column(db.Integer, default=5)  # User selected pages
    word_count = db.Column(db.Integer, default=3750)  # Calculated words

    status = db.Column(db.String(20), default='draft')  # draft, generating, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to chapters
    chapters = db.relationship('ProjectChapter', backref='project', lazy=True, cascade="all, delete-orphan")


class ProjectChapter(db.Model):
    __tablename__ = 'project_chapters'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)  # Generated content stored here

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    topic = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500), nullable=True)  # Cloudinary URL
    extracted_text = db.Column(db.Text, nullable=True)

    ai_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CourseRequirement(db.Model):
    __tablename__ = 'course_requirements'

    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), unique=True, nullable=False)
    advice = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)