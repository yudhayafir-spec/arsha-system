import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'arsha_secret_key_system'

def get_db_connection():
    return mysql.connector.connect(
        host="gateway01.ap-northeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="41V1NDmRAAsJj5J.root",
        password="jWFwGdgJrpaHP0AP",
        database="arsha_db",
        ssl_disabled=False,
        connection_timeout=5
    )

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    session['logged_in'] = True
    session['user'] = 'engineer'
    session['role'] = 'Engineer'
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    total_transaksi = 0
    total_volume = 0.0
    total_profit = 0.0
    pelanggan_unik = 0
    
    profit_harian = 0.0
    profit_mingguan = 0.0
    profit_bulanan = 0.0
    profit_tahunan = 0.0

    chart_labels = ['Juni 2026', 'Juli 2026', 'Agustus 2026', 'September 2026', 'Oktober 2026']
    chart_volumes = [20000000, 18000000, 230000000, 480000000, 415000000]
    logs = []

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
        if res_h: profit_harian = float(res_h['p'])

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        res_m = cursor.fetchone()
        if res_m: profit_mingguan = float(res_m['p'])

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE MONTH(created_at) = MONTH(CURRENT_DATE()) AND YEAR(created_at) = YEAR(CURRENT_DATE())")
        res_b = cursor.fetchone()
        if res_b: profit_bulanan = float(res_b['p'])

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE YEAR(created_at) = YEAR(CURRENT_DATE())")
        res_t = cursor.fetchone()
        if res_t: profit_tahunan = float(res_t['p'])

        # REVISI UTAMA: Menggunakan ORDER BY created_at DESC agar transaksi malam/terbaru pasti muncul di atas
        cursor.execute("SELECT id, created_at, sender_name, recipient_bank, account_number, total_pay, admin_fee FROM transfer_logs ORDER BY created_at DESC, id DESC LIMIT 20")
        logs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as e:
        print("Database Connection Error:", e)

    return render_template(
        'dashboard.html',
        total_transaksi=total_transaksi,
        total_volume=total_volume,
        total_profit=total_profit,
        pelanggan_unik=pelanggan_unik,
        profit_harian=profit_harian,
        profit_mingguan=profit_mingguan,
        profit_bulanan=profit_bulanan,
        profit_tahunan=profit_tahunan,
        chart_labels=chart_labels,
        chart_volumes=chart_volumes,
        logs=logs,
        user='engineer',
        role='Engineer'
    )

@app.route('/transaksi', methods=['GET', 'POST'])
def transaksi():
    receipt = None
    if request.method == 'POST':
        sender_name = request.form.get('sender_name')
        account_number = request.form.get('account_number')
        transaction_type = request.form.get('transaction_type')
        recipient_bank = request.form.get('recipient_bank')
        amount = float(request.form.get('amount') or 0)
        admin_fee = float(request.form.get('admin_fee') or 0)
        total_pay = amount + admin_fee

        receipt = {
            'sender_name': sender_name,
            'account_number': account_number,
            'transaction_type': transaction_type,
            'recipient_bank': recipient_bank,
            'amount': amount,
            'admin_fee': admin_fee,
            'total_pay': total_pay
        }

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transfer_logs (sender_name, account_number, transaction_type, recipient_bank, total_pay, admin_fee, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (sender_name, account_number, transaction_type, recipient_bank, total_pay, admin_fee))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print("Failed to insert to DB:", e)

    return render_template(
        'transaksi.html',
        receipt=receipt,
        user='engineer',
        role='Engineer'
    )

@app.route('/kalkulator', methods=['GET'])
def kalkulator():
    return render_template(
        'kalkulator_modal.html',
        user='engineer',
        role='Engineer'
    )

@app.route('/delete/<int:id>', methods=['GET'])
def delete_transaksi(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transfer_logs WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Failed to delete from DB:", e)
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
