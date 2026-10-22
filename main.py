from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from random import randint

app = Flask(__name__)
app.secret_key = 'arsha_secret_key_123'

# Koneksi ke Database XAMPP (MySQL)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="arsha_db"
    )

# Halaman Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            db.close()
            
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['nama_lengkap'] = user['nama_lengkap']
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Username atau Password salah!")
        except Exception as e:
            return render_template('login.html', error=f"Database error: {str(e)}")
            
    return render_template('login.html')

# Halaman Dashboard Web Utama (Menampilkan Histori Transaksi)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Ambil data histori transaksi dari database
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM transactions ORDER BY id DESC")
    transactions = cursor.fetchall()
    cursor.close()
    db.close()
    
    return render_template('dashboard.html', user=session, active_menu='dashboard', transactions=transactions)

# Halaman Tools Transaksi (Transfer, Top Up, Tarik Tunai + Struk)
@app.route('/transaksi', methods=['GET', 'POST'])
def transaksi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    struk_data = None
    if request.method == 'POST':
        nama = request.form.get('nama_pelanggan')
        wa = request.form.get('no_wa')
        jenis = request.form.get('jenis_transaksi')
        bank = request.form.get('bank_wallet')
        nominal = float(request.form.get('nominal', 0))
        admin = float(request.form.get('admin', 0))
        
        # Simpan transaksi baru ke database MySQL
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO transactions (kode_transaksi, tanggal, nama_pelanggan, transaksi_type, bank_wallet, total_transaksi, admin, profit) 
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s)
        """, ('TRX-' + str(randint(1000, 9999)), nama, jenis, bank, nominal, admin, admin))
        db.commit()
        cursor.close()
        db.close()

        struk_data = {
            'nama': nama,
            'wa': wa,
            'jenis': jenis,
            'bank': bank,
            'nominal': nominal,
            'admin': admin,
            'tanggal': 'Hari Ini'
        }
    return render_template('transaksi.html', user=session, active_menu='transaksi', struk=struk_data)

# Halaman Kalkulator Modal
@app.route('/kalkulator-modal')
def kalkulator_modal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('kalkulator_modal.html', user=session, active_menu='kalkulator')

# Fitur Khusus Super Admin / Engineer: Tambah Akses Staf / CEO
@app.route('/tambah-staf', methods=['GET', 'POST'])
def tambah_staf():
    if 'user_id' not in session or session['role'] != 'super_admin':
        return "Akses ditolak! Fitur ini khusus Super Admin / Engineer.", 403
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nama = request.form['nama_lengkap']
        role = request.form['role']
        
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password, role, nama_lengkap) VALUES (%s, %s, %s, %s)",
                       (username, password, role, nama))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('dashboard'))
        
    return render_template('tambah_staf.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)