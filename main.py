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

    chart_labels = []
    chart_volumes = []
    logs = []

    sort_order = request.args.get('sort', 'DESC').upper()
    if sort_order not in ['ASC', 'DESC']:
        sort_order = 'DESC'

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Ambil parameter tanggal dari URL
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE created_at BETWEEN %s AND %s"
            params = [start_date, end_date]

        # 1. Ringkasan Utama (menyesuaikan filter tanggal jika ada)
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_transaksi, 
                COALESCE(SUM(total_pay), 0) as total_volume, 
                COUNT(DISTINCT sender_name) as pelanggan_unik,
                COALESCE(SUM(admin_fee), 0) as total_profit
            FROM transfer_logs {date_filter}
        """, params)
        summary = cursor.fetchone()
        if summary:
            total_transaksi = summary['total_transaksi']
            total_volume = float(summary['total_volume'])
            pelanggan_unik = summary['pelanggan_unik']
            total_profit = float(summary['total_profit'])

        # 2. Profit Dinamis (Harian, Mingguan, Bulanan, Tahunan)
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

        # 3. Grafik Volume Riil Berdasarkan Data Database
        cursor.execute("""
            SELECT DATE_FORMAT(created_at, '%Y-%m') as bulan, SUM(total_pay) as total_vol 
            FROM transfer_logs 
            GROUP BY bulan 
            ORDER BY bulan ASC 
            LIMIT 6
        """)
        chart_data = cursor.fetchall()
        for row in chart_data:
            chart_labels.append(row['bulan'])
            chart_volumes.append(float(row['total_vol']))

        if not chart_labels:
            chart_labels = ['Belum Ada Data']
            chart_volumes = [0]

        # 4. Histori Transaksi
        query = f"SELECT id, created_at, sender_name, recipient_bank, account_number, total_pay, admin_fee FROM transfer_logs ORDER BY id {sort_order} LIMIT 50"
        cursor.execute(query)
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
        current_sort=sort_order,
        user='engineer',
        role='Engineer'
    )
