#!/usr/bin/env python3
"""
Benutzerverwaltungs-Skript für Wort Bingo

Dieses Skript erstellt neue Benutzer in der Datenbank.
Verwendung: python create_user.py <username> <password> [role]

Beispiele:
    python create_user.py max geheim123 player
    python create_user.py admin admin123 admin
"""

import sys
import os
from werkzeug.security import generate_password_hash

# Flask-App importieren
from app import create_app, db
from models import User

def create_user(username, password, role='player'):
    """Erstellt einen neuen Benutzer"""
    app = create_app()
    
    with app.app_context():
        # Prüfen ob Benutzer bereits existiert
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ Fehler: Benutzer '{username}' existiert bereits!")
            return False
        
        # Neuen Benutzer erstellen
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ Benutzer '{username}' erfolgreich erstellt!")
        print(f"   Rolle: {role}")
        print(f"   Passwort: {password}")
        return True

def list_users():
    """Listet alle Benutzer auf"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("Keine Benutzer gefunden.")
            return
        
        print("\n=== Alle Benutzer ===")
        print(f"{'Username':<20} {'Rolle':<10} {'Punkte':<10}")
        print("-" * 40)
        for user in users:
            print(f"{user.username:<20} {user.role:<10} {user.points:<10}")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  Benutzer erstellen: python create_user.py <username> <password> [role]")
        print("  Benutzer auflisten: python create_user.py --list")
        print("\nRollen: player (Standard), admin")
        sys.exit(1)
    
    if sys.argv[1] == '--list':
        list_users()
    else:
        if len(sys.argv) < 3:
            print("❌ Fehler: Benutzername und Passwort erforderlich!")
            print("Verwendung: python create_user.py <username> <password> [role]")
            sys.exit(1)
        
        username = sys.argv[1]
        password = sys.argv[2]
        role = sys.argv[3] if len(sys.argv) > 3 else 'player'
        
        if role not in ['player', 'admin']:
            print(f"❌ Fehler: Ungültige Rolle '{role}'. Erlaubt: player, admin")
            sys.exit(1)
        
        create_user(username, password, role)
