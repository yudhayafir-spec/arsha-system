import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'arsha_secret_key_system'

def get_db_connection():
    return mysql.connector.connect(
        host="gateway01.ap-northeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="41V1NDmRAAsJj5J.root",
        password="jWFwGdgJrpaHP0AP",
        database="arsha_db",
        ssl_disabled=False
    )

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

    total_transaksi = 333
    total_volume = 1164537527.0
    pelanggan_unik = 71
    total_profit = 6467500.0
    profit_harian = 0.0

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                COUNT(*) as total_transaksi, 
                COALESCE(SUM(total_pay), 0) as total_volume, 
                COUNT(DISTINCT sender_name) as pelanggan_unik,
                COALESCE(SUM(admin_fee), 0) as total_profit
            FROM transfer_logs
        """)
        summary = cursor.fetchone()
        if summary and summary['total_transaksi'] > 0:
            total_transaksi = summary['total_transaksi']
            total_volume = float(summary['total_volume'])
            pelanggan_unik = summary['pelanggan_unik']
            total_profit = float(summary['total_profit'])

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE DATE(created_at) = CURDATE()")
        res_h = cursor.fetchone()
        profit_harian = float(res_h['p']) if res_h and res_h['p'] else 0.0

        cursor.close()
        conn.close()
    except Exception as e:
        print("Database Connection Error:", e)

    return render_template(
        'dashboard.html', 
        total_transaksi=total_transaksi, 
        total_volume=total_volume, 
        pelanggan_unik=pelanggan_unik,
        total_profit=total_profit,
        profit_harian=profit_harian,
        user=session.get('user', 'engineer'), 
        role=session.get('role', 'Engineer')
    )

if __name__ == '__main__':
    app.run(debug=True)
