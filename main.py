import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'arsha_secret_key_system'

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
    # Data statis lengkap sesuai dengan struktur template dashboard.html terbaru
    total_transaksi = 333
    total_volume = 1164537527.0
    total_profit = 6467500.0
    pelanggan_unik = 71
    
    profit_harian = 0.0
    profit_mingguan = 795000.0
    profit_bulanan = 2245000.0
    profit_tahunan = 6467500.0

    chart_labels = ['Juni 2026', 'Juli 2026', 'Agustus 2026', 'September 2026', 'Oktober 2026']
    chart_volumes = [20000000, 18000000, 230000000, 480000000, 415000000]
    
    logs = []

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

if __name__ == '__main__':
    app.run(debug=True)
