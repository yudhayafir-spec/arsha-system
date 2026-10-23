import os
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arsha_secret_key_system'

# --- KONEKSI DATABASE (TiDB Cloud) ---
def get_db_connection():
    return mysql.connector.connect(
        host="gateway01.ap-northeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="41V1NDmRAAsJj5J.root",
        password="jWFwGdgJrpaHP0AP",
        database="arsha_db",  # <-- Sudah diubah ke arsha_db
        ssl_disabled=False
    )

# --- ROUTES ---

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            # Karena di database sudah kita masukkan password hash untuk admin123, 
            # atau cek langsung cocok dengan akun yang kita insert via SQL.
            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['user'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                error = 'Username atau password salah!'
        except Exception as e:
            error = f'Database error: {e}'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    logs = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transfer_logs ORDER BY created_at DESC LIMIT 10")
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        pass

    return render_template('dashboard.html', logs=logs, user=session.get('user'), role=session.get('role'))

@app.route('/transfer', methods=['POST'])
def transfer():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    sender_name = request.form.get('sender_name')
    recipient_bank = request.form.get('recipient_bank')
    account_number = request.form.get('account_number')
    recipient_name = request.form.get('recipient_name')
    try:
        amount = float(request.form.get('amount', 0))
        admin_fee = float(request.form.get('admin_fee', 0))
    except ValueError:
        amount = 0.0
        admin_fee = 0.0
        
    total_pay = amount + admin_fee

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transfer_logs 
            (sender_name, recipient_bank, account_number, recipient_name, amount, admin_fee, total_pay, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (sender_name, recipient_bank, account_number, recipient_name, amount, admin_fee, total_pay, session.get('user')))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        pass

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
