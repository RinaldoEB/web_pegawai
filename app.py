from flask import Flask, render_template, \
    request, redirect, url_for

import pymysql.cursors, os
import datetime
from flask import jsonify

application = Flask(__name__, static_folder='crud/static')

conn = cursor = None

#fungsi koneksi ke basis data
def openDb():
    global conn, cursor
    conn = pymysql.connect(db="db_pegawai", user="root", passwd="",host="localhost",port=3306,autocommit=True)
    cursor = conn.cursor()	

#fungsi menutup koneksi
def closeDb():
    global conn, cursor
    cursor.close()
    conn.close()

#fungsi view index() untuk menampilkan data dari basis data
@application.route('/')
def index():   
    openDb()
    container = []
    sql = "SELECT * FROM pegawai ORDER BY NIK DESC;"
    cursor.execute(sql)
    results = cursor.fetchall()
    for data in results:
        container.append(data)
    closeDb()
    return render_template('index.html', container=container)


#fungsi membuat NIK otomatis
def generate_nik():
    #mengambil koneksi database
    openDb()
    
    #Query untuk mendapatkan NIK terakhir dari database
    cursor.execute("SELECT NIK FROM pegawai ORDER BY NIK DESC LIMIT 1")
    last_nik = cursor.fetchone()
    
    if last_nik :
        #mengambil nomor urut terakhir
        last_number = int(last_nik[0])
        next_number = last_number + 1
    else :
        #jika tidak ada data, berarti mulai dari 1
        next_number = 1
    
    #format nomor urut dengan leading zeros (00001, 00002, dst)
    next_nik = f"{next_number:04}"
    
    #menutup koneksi database
    closeDb()
    return next_nik

#fungsi untuk menyimpan lokasi foto
UPLOAD_FOLDER = 'crud/static/foto/'
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#fungsi view tambah() untuk membuat form tambah data
@application.route('/tambah', methods=['GET','POST'])
def tambah():
    generated_nik = generate_nik()  # Memanggil fungsi untuk mendapatkan NIK otomatis
    
    if request.method == 'POST':
        nik = request.form['nik']
        nama = request.form['nama']
        alamat = request.form['alamat']
        tgllahir = request.form['tgllahir']
        jeniskelamin = request.form['jeniskelamin']
        status = request.form['status']
        gaji = request.form['gaji']
        foto = request.form['nik']

        # Pastikan direktori upload ada
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Simpan foto dengan nama NIK
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                foto.save(os.path.join(application.config['UPLOAD_FOLDER'], f"{nik}.jpg"))

        openDb()
        sql = "INSERT INTO pegawai (nik,nama,alamat,tgllahir,jeniskelamin,status,gaji,foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (nik,nama,alamat,tgllahir,jeniskelamin,status,gaji,foto)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        return redirect(url_for('index'))        
    else:
        return render_template('tambah.html', nik=generated_nik)  # Mengirimkan NIK otomatis ke template
    
#fungsi view edit() untuk form edit data
@application.route('/edit/<nik>', methods=['GET','POST'])
def edit(nik):
    openDb()
    cursor.execute('SELECT * FROM pegawai WHERE nik=%s', (nik))
    data = cursor.fetchone()
    if request.method == 'POST':
        nik = request.form['nik']
        nama = request.form['nama']
        alamat = request.form['alamat']
        tgllahir = request.form['tgllahir']
        jeniskelamin = request.form['jeniskelamin']
        status = request.form['status']
        gaji = request.form['gaji']
        foto = request.form['nik']

        path_to_photo = os.path.join(application.root_path, 'foto', f'{nik}.jpg')
        if os.path.exists(path_to_photo):
            os.remove(path_to_photo)

        # Pastikan direktori upload ada
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Simpan foto dengan nama NIK
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                foto.save(os.path.join(application.config['UPLOAD_FOLDER'], f"{nik}.jpg"))
        sql = "UPDATE pegawai SET nama=%s, alamat=%s, tgllahir=%s, jeniskelamin=%s, status=%s, gaji=%s, foto=%s WHERE nik=%s"
        val = (nama, alamat, tgllahir,jeniskelamin, status, gaji, foto, nik)
        cursor.execute(sql, val)
        conn.commit()
        closeDb()
        return redirect(url_for('index'))
    else:
        closeDb()
        return render_template('edit.html', data=data)

#fungsi menghapus data
@application.route('/hapus/<nik>', methods=['GET','POST'])
def hapus(nik):
    openDb()
    cursor.execute('DELETE FROM pegawai WHERE nik=%s', (nik,))
    # Hapus foto berdasarkan NIK
    path_to_photo = os.path.join(application.root_path, 'crud/static/foto/', f'{nik}.jpg')
    if os.path.exists(path_to_photo):
        os.remove(path_to_photo)

    conn.commit()
    closeDb()
    return redirect(url_for('index'))

#fungsi cetak ke PDF
@application.route('/get_employee_data/<nik>', methods=['GET'])
def get_employee_data(nik):
    # Koneksi ke database
    connection = pymysql.connect(host='localhost',
                                 user='root',
                                 password='',  # Password Anda (jika ada)
                                 db='db_pegawai',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            # Query untuk mengambil data pegawai berdasarkan NIK
            sql = "SELECT * FROM pegawai WHERE nik = %s"
            cursor.execute(sql, (nik,))
            employee_data = cursor.fetchone()  # Mengambil satu baris data pegawai

            # Log untuk melihat apakah permintaan diterima dengan benar
            print("Menerima permintaan untuk NIK:", nik)

            # Log untuk melihat data yang dikirim ke klien
            print("Data yang dikirim:", employee_data)

            return jsonify(employee_data)  # Mengembalikan data sebagai JSON

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Terjadi kesalahan saat mengambil data'}), 500

    finally:
        connection.close()  # Menutup koneksi database setelah selesai

#Program utama      
if __name__ == '__main__':
    application.run(debug=True)
