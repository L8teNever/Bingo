from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Benutzer-Modell für Authentifizierung und Punkteverwaltung"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='player')  # 'admin' or 'player'
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to words submitted by this user
    words = db.relationship('WordLog', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username} (Role: {self.role}, Points: {self.points})>'

class WordLog(db.Model):
    """Log für eingereichte Wörter pro Benutzer und Tag"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now().date(), index=True)
    is_locked = db.Column(db.Boolean, default=False)
    changes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite Index für schnelle Abfragen
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'date'),
        db.Index('idx_word_date', 'word', 'date'),
    )
    
    def __repr__(self):
        return f'<WordLog {self.word} by User#{self.user_id} on {self.date}>'

class CooldownLog(db.Model):
    """Cooldown-Verwaltung für bereits verwendete Wörter"""
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expiry_date = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CooldownLog {self.word} until {self.expiry_date}>'
    
    def is_active(self):
        """Prüft ob der Cooldown noch aktiv ist"""
        return self.expiry_date > datetime.now().date()

class Setting(db.Model):
    """Anwendungseinstellungen"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False, index=True)
    value = db.Column(db.String(200), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'

class Subscription(db.Model):
    """Push-Benachrichtigungen (für zukünftige Erweiterungen)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    subscription_info = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription for User#{self.user_id}>'

