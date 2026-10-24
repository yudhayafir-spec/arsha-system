import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

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

# PWA SERVING
@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.root_path, 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory(app.root_path, 'sw.js')

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

# DASHBOARD DESKTOP LAMA (TIDAK BERUBAH)
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session.get('user'), role=session.get('role'))

# APLIKASI MOBILE ARSHA GROUP (KHUSUS HP / PWA)
@app.route('/mobile', methods=['GET'])
def mobile_app():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    logs = []
    total_transaksi = 0
    total_volume = 0.0
    pelanggan_unik = 0
    total_profit = 0.0
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
        if summary:
            total_transaksi = summary['total_transaksi']
            total_volume = float(summary['total_volume'])
            pelanggan_unik = summary['pelanggan_unik']
            total_profit = float(summary['total_profit'])

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE DATE(created_at) = CURDATE()")
        res_h = cursor.fetchone()
        profit_harian = float(res_h['p']) if res_h and res_h['p'] else 0.0

        cursor.execute("SELECT * FROM transfer_logs ORDER BY created_at DESC LIMIT 50")
        logs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as e:
        print("Mobile App Error:", e)

    return render_template(
        'index.html', 
        logs=logs, 
        total_transaksi=total_transaksi, 
        total_volume=total_volume, 
        pelanggan_unik=pelanggan_unik,
        total_profit=total_profit,
        profit_harian=profit_harian,
        user=session.get('user'), 
        role=session.get('role')
    )

@app.route('/mobile/transaksi', methods=['POST'])
def mobile_transaksi():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    data = request.form
    try:
        sender_name = data.get('sender_name') or 'Umum'
        account_number = data.get('account_number') or '-'
        recipient_bank = data.get('recipient_bank') or 'BRI'
        total_pay = float(data.get('amount') or 0)
        admin_fee = float(data.get('admin_fee') or 0)
        amount = total_pay - admin_fee

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transfer_logs 
            (sender_name, recipient_bank, account_number, recipient_name, amount, admin_fee, total_pay, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (sender_name, recipient_bank, account_number, sender_name, amount, admin_fee, total_pay, session.get('user')))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Transaction Error:", e)

    return redirect(url_for('mobile_app'))

@app.route('/mobile/delete/<int:id>', methods=['GET'])
def mobile_delete(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transfer_logs WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Delete Error:", e)
    return redirect(url_for('mobile_app'))

if __name__ == '__main__':
    app.run(debug=True)
