from app import app, init_db

if __name__ == '__main__':
    init_db()
    print("Dinner Bingo Server gestartet!")
    print("Admin-Login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
