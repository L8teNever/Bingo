from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='player') # 'admin' or 'player'
    points = db.Column(db.Integer, default=0)
    
    # Relationship to words submitted by this user
    words = db.relationship('WordLog', backref='user', lazy=True)

class WordLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now().date())
    is_locked = db.Column(db.Boolean, default=False)
    changes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())

class CooldownLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_info = db.Column(db.Text, nullable=False) # JSON string
