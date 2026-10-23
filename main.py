import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
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

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    logs = []
    total_transaksi = 0
    total_volume = 0.0
    pelanggan_unik = 0
    
    profit_harian = 0.0
    profit_mingguan = 0.0
    profit_bulanan = 0.0
    profit_tahunan = 0.0

    chart_labels = []
    chart_volumes = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []

        if start_date and end_date:
            where_clauses.append("created_at >= %s AND created_at <= CONCAT(%s, ' 23:59:59')")
            params.extend([start_date, end_date])
        elif start_date:
            where_clauses.append("created_at >= %s")
            params.append(start_date)
        elif end_date:
            where_clauses.append("created_at <= CONCAT(%s, ' 23:59:59')")
            params.append(end_date)

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        # 1. Total Ringkasan
        query_summary = f"""
            SELECT 
                COUNT(*) as total_transaksi, 
                COALESCE(SUM(total_pay), 0) as total_volume, 
                COUNT(DISTINCT sender_name) as pelanggan_unik 
            FROM transfer_logs {where_sql}
        """
        cursor.execute(query_summary, tuple(params))
        summary = cursor.fetchone()
        if summary:
            total_transaksi = summary['total_transaksi']
            total_volume = float(summary['total_volume'])
            pelanggan_unik = summary['pelanggan_unik']

        # 2. Rekapitulasi Profit Dinamis dari Database
        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE DATE(created_at) = CURDATE()")
        res_h = cursor.fetchone()
        profit_harian = float(res_h['p']) if res_h and res_h['p'] else 0.0
        
        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE YEARWEEK(created_at, 1) = YEARWEEK(CURDATE(), 1)")
        res_m = cursor.fetchone()
        profit_mingguan = float(res_m['p']) if res_m and res_m['p'] else 0.0

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())")
        res_b = cursor.fetchone()
        profit_bulanan = float(res_b['p']) if res_b and res_b['p'] else 0.0

        cursor.execute("SELECT COALESCE(SUM(admin_fee), 0) as p FROM transfer_logs WHERE YEAR(created_at) = YEAR(CURDATE())")
        res_t = cursor.fetchone()
        profit_tahunan = float(res_t['p']) if res_t and res_t['p'] else 0.0

        # 3. Data Grafik PER BULAN (Monthly Aggregation)
        query_chart = f"""
            SELECT DATE_FORMAT(created_at, '%Y-%m') as bulan, SUM(total_pay) as vol 
            FROM transfer_logs {where_sql}
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY bulan ASC
        """
        cursor.execute(query_chart, tuple(params))
        chart_rows = cursor.fetchall()
        for r in chart_rows:
            # Ubah format '2026-06' jadi 'Juni 2026' agar rapi dibaca
            parts = r['bulan'].split('-')
            months_id = {'01':'Januari', '02':'Februari', '03':'Maret', '04':'April', '05':'Mei', '06':'Juni', '07':'Juli', '08':'Agustus', '09':'September', '10':'Oktober', '11':'November', '12':'Desember'}
            m_name = months_id.get(parts[1], parts[1])
            chart_labels.append(f"{m_name} {parts[0]}")
            chart_volumes.append(float(r['vol']))

        # 4. Tabel Histori Transaksi Terbaru
        query_logs = f"SELECT * FROM transfer_logs {where_sql} ORDER BY created_at DESC LIMIT 50"
        cursor.execute(query_logs, tuple(params))
        logs = cursor.fetchall()

        cursor.close()
        conn.close()
    except Exception as e:
        print("Dashboard Error:", e)

    return render_template(
        'dashboard.html', 
        logs=logs, 
        total_transaksi=total_transaksi, 
        total_volume=total_volume, 
        pelanggan_unik=pelanggan_unik,
        profit_harian=profit_harian,
        profit_mingguan=profit_mingguan,
        profit_bulanan=profit_bulanan,
        profit_tahunan=profit_tahunan,
        chart_labels=chart_labels,
        chart_volumes=chart_volumes,
        user=session.get('user'), 
        role=session.get('role')
    )

@app.route('/transaksi', methods=['GET'])
def transaksi():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('transaksi.html', user=session.get('user'), role=session.get('role'))

@app.route('/kalkulator', methods=['GET'])
@app.route('/kalkulator-modal', methods=['GET'])
@app.route('/kalkulator_modal', methods=['GET'])
@app.route('/calculator', methods=['GET'])
def kalkulator_view():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('kalkulator_modal.html', user=session.get('user'), role=session.get('role'))

@app.route('/seed-database')
def seed_database():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        excel_path = "ATMS DATABASE.xlsx"
        df = pd.read_excel(excel_path, sheet_name="Transaksi")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE transfer_logs")
        for idx, row in df.iterrows():
            sender_name = str(row['Nama']) if pd.notna(row['Nama']) else 'Umum'
            bank_wallet = str(row['Bank/Wallet']) if pd.notna(row['Bank/Wallet']) else 'BRI'
            transaction_type = str(row['Transaksi Type']) if pd.notna(row['Transaksi Type']) else 'Transfer'
            total_pay = float(row['Total Transaksi']) if pd.notna(row['Total Transaksi']) else 0.0
            admin_fee = float(row['Admin']) if pd.notna(row['Admin']) else 0.0
            amount = total_pay - admin_fee
            created_at = str(row['Tanggal'])
            cursor.execute("""
                INSERT INTO transfer_logs 
                (sender_name, recipient_bank, account_number, recipient_name, amount, admin_fee, total_pay, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (sender_name, bank_wallet, transaction_type, sender_name, amount, admin_fee, total_pay, session.get('user'), created_at))
        conn.commit()
        cursor.close()
        conn.close()
        return "BERHASIL MIGRASI 333 DATA EXCEL KE DATABASE!"
    except Exception as e:
        return f"Gagal migrasi: {e}"

if __name__ == '__main__':
    app.run(debug=True)
