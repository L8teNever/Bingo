from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, WordLog, CooldownLog, Setting, Subscription
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bingo-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bingo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        db.create_all()
        # Default settings
        defaults = {
            'notify_time': '12:00',
            'dinner_time': '18:00',
            'cooldown_days': '14',
            'max_changes': '3'
        }
        for key, value in defaults.items():
            if not Setting.query.filter_by(key=key).first():
                db.session.add(Setting(key=key, value=value))
        
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin', 
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Ungültiger Benutzername oder Passwort')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now().date()
    now_time = datetime.now().strftime('%H:%M')
    
    # Get settings
    notify_time = Setting.query.filter_by(key='notify_time').first().value
    dinner_time = Setting.query.filter_by(key='dinner_time').first().value
    
    # State flags
    is_open = now_time >= notify_time and now_time < dinner_time
    is_dinner = now_time >= dinner_time
    
    user_word = WordLog.query.filter_by(user_id=current_user.id, date=today).first()
    
    all_words = []
    if user_word or is_dinner:
        # Show all words if user submitted or if dinner has started
        all_words = WordLog.query.filter_by(date=today).all()
    
    leaderboard = User.query.order_by(User.points.desc()).all()
    
    return render_template('dashboard.html', 
                           user_word=user_word, 
                           all_words=all_words,
                           leaderboard=leaderboard,
                           notify_time=notify_time,
                           dinner_time=dinner_time,
                           is_open=is_open,
                           is_dinner=is_dinner)

@app.route('/submit_word', methods=['POST'])
@login_required
def submit_word():
    word = request.form.get('word').strip().lower()
    if not word:
        flash('Wort darf nicht leer sein')
        return redirect(url_for('dashboard'))
    
    today = datetime.now().date()
    now_time = datetime.now().strftime('%H:%M')
    
    notify_time = Setting.query.filter_by(key='notify_time').first().value
    dinner_time = Setting.query.filter_by(key='dinner_time').first().value
    
    if now_time < notify_time:
        flash(f'Die Eingabe startet erst um {notify_time} Uhr.')
        return redirect(url_for('dashboard'))
        
    if now_time >= dinner_time:
        flash('Das Essen hat bereits begonnen. Keine Änderungen mehr möglich.')
        return redirect(url_for('dashboard'))

    # Check cooldown
    cooldown = CooldownLog.query.filter_by(word=word).first()
    if cooldown and cooldown.expiry_date > today:
        flash(f'Dieses Wort steht noch unter Cooldown bis zum {cooldown.expiry_date}')
        return redirect(url_for('dashboard'))

    # Check duplicates for today
    duplicate = WordLog.query.filter_by(word=word, date=today).first()
    if duplicate and duplicate.user_id != current_user.id:
        flash('Dieses Wort wurde heute bereits von jemand anderem gewählt.')
        return redirect(url_for('dashboard'))

    # Check changes limit
    max_changes = int(Setting.query.filter_by(key='max_changes').first().value)
    existing_log = WordLog.query.filter_by(user_id=current_user.id, date=today).first()
    
    if existing_log:
        if existing_log.word != word:
            if existing_log.changes_count >= max_changes:
                flash('Du hast das Limit für Wortänderungen heute erreicht.')
                return redirect(url_for('dashboard'))
            existing_log.word = word
            existing_log.changes_count += 1
    else:
        new_log = WordLog(user_id=current_user.id, word=word, date=today)
        db.session.add(new_log)
    
    db.session.commit()
    flash('Wort erfolgreich eingeloggt!')
    return redirect(url_for('dashboard'))

@app.route('/withdraw_word', methods=['POST'])
@login_required
def withdraw_word():
    today = datetime.now().date()
    now_time = datetime.now().strftime('%H:%M')
    dinner_time = Setting.query.filter_by(key='dinner_time').first().value
    
    if now_time >= dinner_time:
        flash('Das Essen hat bereits begonnen. Zurückziehen nicht mehr möglich.')
        return redirect(url_for('dashboard'))
        
    WordLog.query.filter_by(user_id=current_user.id, date=today).delete()
    db.session.commit()
    flash('Wort zurückgezogen.')
    return redirect(url_for('dashboard'))

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    voted_user_id = request.form.get('voted_user_id')
    voted_user = User.query.get(voted_user_id)
    
    if voted_user:
        voted_user.points += 1
        
        # Add word to cooldown
        today = datetime.now().date()
        user_word = WordLog.query.filter_by(user_id=voted_user.id, date=today).first()
        if user_word:
            cooldown_days = int(Setting.query.filter_by(key='cooldown_days').first().value)
            expiry = today + timedelta(days=cooldown_days)
            cd = CooldownLog.query.filter_by(word=user_word.word).first()
            if cd:
                cd.expiry_date = expiry
            else:
                db.session.add(CooldownLog(word=user_word.word, expiry_date=expiry))
        
        db.session.commit()
        flash(f'Punkt vergeben an {voted_user.username}!')
    
    return redirect(url_for('dashboard'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        return "Zugriff verweigert", 403
    
    if request.method == 'POST':
        if 'create_user' in request.form:
            username = request.form.get('new_username')
            password = request.form.get('new_password')
            role = request.form.get('role', 'player')
            if User.query.filter_by(username=username).first():
                flash('Benutzer existiert bereits')
            else:
                new_user = User(username=username, password_hash=generate_password_hash(password), role=role)
                db.session.add(new_user)
                db.session.commit()
                flash('Benutzer erstellt')
        
        elif 'update_settings' in request.form:
            for key in ['notify_time', 'dinner_time', 'cooldown_days', 'max_changes']:
                setting = Setting.query.filter_by(key=key).first()
                if setting:
                    setting.value = request.form.get(key)
            db.session.commit()
            flash('Einstellungen aktualisiert')

        elif 'reward_points' in request.form:
            user_id = request.form.get('user_id')
            user = User.query.get(user_id)
            if user:
                user.points += 1
                db.session.commit()
                flash(f'Punkt vergeben an {user.username}')

    users = User.query.all()
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template('admin.html', users=users, settings=settings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
