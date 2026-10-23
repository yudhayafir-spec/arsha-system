import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
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
        database="sys",
        ssl_disabled=False
    )

# --- INISIALISASI TABEL & AKUN DEFAULT ---
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Tabel Users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL
            )
        """)

        # 2. Tabel Transfer Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_name VARCHAR(100),
                recipient_bank VARCHAR(50),
                account_number VARCHAR(50),
                recipient_name VARCHAR(100),
                amount DECIMAL(15, 2),
                admin_fee DECIMAL(15, 2),
                total_pay DECIMAL(15, 2),
                status VARCHAR(20) DEFAULT 'Success',
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Cek apakah akun engineer sudah ada
        cursor.execute("SELECT * FROM users WHERE username = 'engineer'")
        engineer = cursor.fetchone()
        if not engineer:
            hashed_pw = generate_password_hash("admin123")
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                           ('engineer', hashed_pw, 'Engineer'))
            conn.commit()

        cursor.close()
        conn.close()
    except Exception as e:
        print("Database Init Error:", e)

# Jalankan inisialisasi tabel saat aplikasi start
init_db()

# --- ROUTES ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
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

            if user and check_password_hash(user['password'], password):
                session['user'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                flash('Username atau password salah!', 'danger')
        except Exception as e:
            flash(f'Database error: {e}', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM transfer_logs ORDER BY created_at DESC LIMIT 10")
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        logs = []

    return render_template('dashboard.html', logs=logs, user=session['user'], role=session.get('role', 'Staff'))

@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user' not in session:
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
        """, (sender_name, recipient_bank, account_number, recipient_name, amount, admin_fee, total_pay, session['user']))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        pass

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
