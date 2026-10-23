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

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Buat klausa WHERE dinamis berdasarkan filter tanggal
        where_clauses = []
        params = []

        if start_date and end_date:
            where_clauses.append("DATE(created_at) BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        elif start_date:
            where_clauses.append("DATE(created_at) >= %s")
            params.append(start_date)
        elif end_date:
            where_clauses.append("DATE(created_at) <= %s")
            params.append(end_date)

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        # 1. Ambil Ringkasan Statistik SESUAI FILTER TANGGAL
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
            total_volume = summary['total_volume']
            pelanggan_unik = summary['pelanggan_unik']

        # 2. Ambil Log Transaksi untuk Tabel (dengan filter yang sama)
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
        user=session.get('user'), 
        role=session.get('role')
    )
