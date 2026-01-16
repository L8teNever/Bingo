from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, WordLog, CooldownLog, Setting, Subscription
from datetime import datetime, timedelta
import logging
import os

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application Factory für bessere Testbarkeit und Struktur"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Konfiguration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bingo-secret-key-123')
    
    # Datenbank-Pfad konfigurieren (Priorität: Umgebungsvariable > Instance-Ordner)
    if os.environ.get('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    else:
        # Standard: sqlite:///app/instance/bingo.db (im Container)
        db_path = os.path.join(app.instance_path, 'bingo.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        os.makedirs(app.instance_path, exist_ok=True)
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    logger.info(f"Nutze Datenbank: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Extensions initialisieren
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Fehler beim Laden des Users {user_id}: {e}")
            return None
    
    # Datenbankinitialisierung
    with app.app_context():
        try:
            db.create_all()
            init_default_data()
            create_users_from_env()  # Benutzer aus Umgebungsvariable erstellen
            logger.info("Datenbank erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankinitialisierung: {e}")
    
    # Routen registrieren
    register_routes(app)
    
    # Error Handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template('login.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        logger.error(f"Interner Serverfehler: {e}")
        flash('Ein interner Fehler ist aufgetreten. Bitte versuche es erneut.')
        return redirect(url_for('dashboard'))
    
    return app

def init_default_data():
    """Initialisiert Standarddaten in der Datenbank"""
    try:
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
            logger.info("Standard-Admin-Benutzer erstellt")
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Initialisieren der Standarddaten: {e}")
        raise

def create_users_from_env():
    """Erstellt Benutzer aus USERS Umgebungsvariable
    
    Format: username:password:role,username:password:role,...
    Beispiel: USERS=max:geheim123:player,anna:test456:player,admin:admin123:admin
    """
    users_env = os.environ.get('USERS', '')
    if not users_env:
        logger.info("Keine USERS Umgebungsvariable gefunden, überspringe Benutzererstellung")
        return
    
    try:
        user_definitions = users_env.split(',')
        created_count = 0
        updated_count = 0
        
        for user_def in user_definitions:
            user_def = user_def.strip()
            if not user_def:
                continue
            
            parts = user_def.split(':')
            if len(parts) != 3:
                logger.warning(f"Ungültiges Benutzerformat: {user_def} (erwartet: username:password:role)")
                continue
            
            username, password, role = parts
            username = username.strip()
            password = password.strip()
            role = role.strip()
            
            if role not in ['player', 'admin']:
                logger.warning(f"Ungültige Rolle für {username}: {role} (erwartet: player oder admin)")
                continue
            
            # Prüfen ob Benutzer existiert
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                # Benutzer existiert - Passwort und Rolle aktualisieren
                existing_user.password_hash = generate_password_hash(password)
                existing_user.role = role
                updated_count += 1
                logger.info(f"Benutzer aktualisiert: {username} (Rolle: {role})")
            else:
                # Neuen Benutzer erstellen
                new_user = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                    role=role
                )
                db.session.add(new_user)
                created_count += 1
                logger.info(f"Neuer Benutzer erstellt: {username} (Rolle: {role})")
        
        db.session.commit()
        
        if created_count > 0 or updated_count > 0:
            logger.info(f"Benutzerverwaltung abgeschlossen: {created_count} erstellt, {updated_count} aktualisiert")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Fehler beim Erstellen von Benutzern aus Umgebungsvariable: {e}")
        raise

def register_routes(app):
    """Registriert alle Routen"""
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            try:
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '')
                
                if not username or not password:
                    flash('Bitte Benutzername und Passwort eingeben')
                    return render_template('login.html')
                
                user = User.query.filter_by(username=username).first()
                if user and check_password_hash(user.password_hash, password):
                    login_user(user)
                    logger.info(f"Benutzer {username} erfolgreich eingeloggt")
                    return redirect(url_for('dashboard'))
                
                flash('Ungültiger Benutzername oder Passwort')
                logger.warning(f"Fehlgeschlagener Login-Versuch für Benutzer: {username}")
            except Exception as e:
                logger.error(f"Fehler beim Login: {e}")
                flash('Ein Fehler ist aufgetreten. Bitte versuche es erneut.')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        username = current_user.username
        logout_user()
        logger.info(f"Benutzer {username} ausgeloggt")
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        try:
            today = datetime.now().date()
            now_time = datetime.now().strftime('%H:%M')
            
            # Get settings
            notify_time_setting = Setting.query.filter_by(key='notify_time').first()
            dinner_time_setting = Setting.query.filter_by(key='dinner_time').first()
            
            if not notify_time_setting or not dinner_time_setting:
                logger.error("Zeiteinstellungen nicht gefunden")
                flash('Konfigurationsfehler. Bitte kontaktiere den Administrator.')
                return redirect(url_for('settings'))
            
            notify_time = notify_time_setting.value
            dinner_time = dinner_time_setting.value
            
            # State flags
            is_open = now_time >= notify_time and now_time < dinner_time
            is_dinner = now_time >= dinner_time
            
            user_word = WordLog.query.filter_by(user_id=current_user.id, date=today).first()
            
            all_words = []
            if user_word or is_dinner:
                # Show all words if user submitted or if dinner has started
                all_words = WordLog.query.filter_by(date=today).all()
            
            return render_template('dashboard.html', 
                                   user_word=user_word, 
                                   all_words=all_words,
                                   notify_time=notify_time,
                                   dinner_time=dinner_time,
                                   is_open=is_open,
                                   is_dinner=is_dinner)
        except Exception as e:
            logger.error(f"Fehler im Dashboard: {e}")
            flash('Ein Fehler ist aufgetreten beim Laden des Dashboards.')
            return redirect(url_for('login'))
    
    @app.route('/leaderboard')
    @login_required
    def leaderboard():
        try:
            users = User.query.order_by(User.points.desc()).all()
            return render_template('leaderboard.html', users=users)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Bestenliste: {e}")
            flash('Fehler beim Laden der Bestenliste.')
            return redirect(url_for('dashboard'))
    
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html')
    
    @app.route('/submit_word', methods=['POST'])
    @login_required
    def submit_word():
        try:
            word = request.form.get('word', '').strip().lower()
            if not word:
                flash('Wort darf nicht leer sein')
                return redirect(url_for('dashboard'))
            
            # Validierung: Nur Buchstaben und Leerzeichen
            if not all(c.isalpha() or c.isspace() for c in word):
                flash('Wort darf nur Buchstaben enthalten')
                return redirect(url_for('dashboard'))
            
            if len(word) > 100:
                flash('Wort ist zu lang (max. 100 Zeichen)')
                return redirect(url_for('dashboard'))
            
            today = datetime.now().date()
            now_time = datetime.now().strftime('%H:%M')
            
            notify_time = Setting.query.filter_by(key='notify_time').first().value
            dinner_time = Setting.query.filter_by(key='dinner_time').first().value
            
            if now_time < notify_time:
                flash('Die Eingabe startet erst um {notify_time} Uhr.')
                return redirect(url_for('dashboard'))
                
            if now_time >= dinner_time:
                flash('Die Abstimmungsphase hat bereits begonnen. Keine Änderungen mehr möglich.')
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
            logger.info(f"Benutzer {current_user.username} hat Wort '{word}' eingereicht")
            flash('Wort erfolgreich eingeloggt!')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fehler beim Einreichen des Wortes: {e}")
            flash('Fehler beim Speichern des Wortes. Bitte versuche es erneut.')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/withdraw_word', methods=['POST'])
    @login_required
    def withdraw_word():
        try:
            today = datetime.now().date()
            now_time = datetime.now().strftime('%H:%M')
            dinner_time = Setting.query.filter_by(key='dinner_time').first().value
            
            if now_time >= dinner_time:
                flash('Die Abstimmungsphase hat bereits begonnen. Zurückziehen nicht mehr möglich.')
                return redirect(url_for('dashboard'))
            
            deleted_count = WordLog.query.filter_by(user_id=current_user.id, date=today).delete()
            db.session.commit()
            
            if deleted_count > 0:
                logger.info(f"Benutzer {current_user.username} hat Wort zurückgezogen")
                flash('Wort zurückgezogen.')
            else:
                flash('Kein Wort zum Zurückziehen gefunden.')
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fehler beim Zurückziehen des Wortes: {e}")
            flash('Fehler beim Zurückziehen des Wortes.')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/vote', methods=['POST'])
    @login_required
    def vote():
        try:
            voted_user_id = request.form.get('voted_user_id')
            if not voted_user_id:
                flash('Ungültige Abstimmung')
                return redirect(url_for('dashboard'))
            
            voted_user = User.query.get(voted_user_id)
            
            if not voted_user:
                flash('Benutzer nicht gefunden')
                return redirect(url_for('dashboard'))
            
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
            logger.info(f"Punkt vergeben an {voted_user.username} von {current_user.username}")
            flash(f'Punkt vergeben an {voted_user.username}!')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fehler beim Abstimmen: {e}")
            flash('Fehler beim Vergeben des Punktes.')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/change_password', methods=['POST'])
    @login_required
    def change_password():
        try:
            new_password = request.form.get('new_password', '').strip()
            if not new_password:
                flash('Passwort darf nicht leer sein')
                return redirect(url_for('settings'))
            
            if len(new_password) < 4:
                flash('Passwort muss mindestens 4 Zeichen lang sein')
                return redirect(url_for('settings'))
            
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            logger.info(f"Benutzer {current_user.username} hat Passwort geändert")
            flash('Passwort erfolgreich geändert!')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fehler beim Ändern des Passworts: {e}")
            flash('Fehler beim Ändern des Passworts.')
        
        return redirect(url_for('settings'))
    
    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin_panel():
        if current_user.role != 'admin':
            logger.warning(f"Unbefugter Zugriff auf Admin-Panel von {current_user.username}")
            return "Zugriff verweigert", 403
        
        try:
            if request.method == 'POST':
                if 'update_settings' in request.form:
                    for key in ['notify_time', 'dinner_time', 'cooldown_days', 'max_changes']:
                        setting = Setting.query.filter_by(key=key).first()
                        if setting:
                            setting.value = request.form.get(key)
                    db.session.commit()
                    logger.info("Einstellungen aktualisiert")
                    flash('Einstellungen aktualisiert')
                
                elif 'reward_points' in request.form:
                    user_id = request.form.get('user_id')
                    new_points = request.form.get('points')
                    user = User.query.get(user_id)
                    if user and new_points:
                        user.points = int(new_points)
                        db.session.commit()
                        logger.info(f"Punkte für {user.username} auf {new_points} gesetzt")
                        flash(f'Punkte für {user.username} auf {new_points} gesetzt.')
            
            users = User.query.all()
            settings = {s.key: s.value for s in Setting.query.all()}
            return render_template('admin.html', users=users, settings=settings)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fehler im Admin-Panel: {e}")
            flash('Ein Fehler ist aufgetreten.')
            return redirect(url_for('dashboard'))

# Für direkte Ausführung
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
