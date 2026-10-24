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
    # Angka real ATMS sesuai data awal
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
    
    logs = [
        {"id": 1, "created_at": "24-10-2026 14:00", "sender_name": "Budi Santoso", "recipient_bank": "BRI", "account_number": "1234567890", "total_pay": 500000.0, "admin_fee": 10000.0},
        {"id": 2, "created_at": "24-10-2026 15:30", "sender_name": "Siti Aminah", "recipient_bank": "BCA", "account_number": "0987654321", "total_pay": 1250000.0, "admin_fee": 15000.0}
    ]

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
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
