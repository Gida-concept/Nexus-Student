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
        active_sub = Subscription.query.filter_by(
            user_id=self.id, 
            status='active'
        ).first()
        return bool(active_sub)
