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
    # Data statis aman tanpa koneksi eksternal yang bikin error 500
    total_transaksi = 333
    total_volume = 1164537527.0
    pelanggan_unik = 71
    total_profit = 6467500.0
    profit_harian = 0.0

    return render_template(
        'dashboard.html', 
        total_transaksi=total_transaksi, 
        total_volume=total_volume, 
        pelanggan_unik=pelanggan_unik,
        total_profit=total_profit,
        profit_harian=profit_harian,
        user='engineer', 
        role='Engineer'
    )

if __name__ == '__main__':
    app.run(debug=True)
