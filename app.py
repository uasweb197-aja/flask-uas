import os
import sqlite3
import uuid
import base64
import time
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import qrcode
from export_pdf import calculate_books_hash, generate_pdf_buffer

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'flask-book-manager-secret-key-12345')

if os.environ.get('VERCEL'):
    DATABASE = '/tmp/books.db'
else:
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'books.db')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_dir = os.path.dirname(DATABASE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            judul TEXT NOT NULL,
            penulis TEXT NOT NULL,
            penerbit TEXT NOT NULL
        )
    ''')
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM books')
    if cursor.fetchone()[0] == 0:
        sample_books = [
            (str(uuid.uuid4()), 'Laskar Pelangi', 'Andrea Hirata', 'Bentang Pustaka'),
            (str(uuid.uuid4()), 'Bumi Manusia', 'Pramoedya Ananta Toer', 'Lentera Dipantara'),
            (str(uuid.uuid4()), 'Filosofi Kopi', 'Dee Lestari', 'Truewriting')
        ]
        cursor.executemany('INSERT INTO books (id, judul, penulis, penerbit) VALUES (?, ?, ?, ?)', sample_books)
        conn.commit()
    
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        judul = request.form.get('judul', '').strip()
        penulis = request.form.get('penulis', '').strip()
        penerbit = request.form.get('penerbit', '').strip()
        
        if not judul or not penulis or not penerbit:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('add_book'))
        
        book_id = str(uuid.uuid4())
        
        try:
            conn = get_db()
            conn.execute('INSERT INTO books (id, judul, penulis, penerbit) VALUES (?, ?, ?, ?)', (book_id, judul, penulis, penerbit))
            conn.commit()
            conn.close()
            flash('Buku berhasil ditambahkan!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Gagal menambahkan buku: {str(e)}', 'danger')
            return redirect(url_for('add_book'))
    
    return render_template('add.html')

@app.route('/edit/<book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    conn = get_db()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    
    if not book:
        flash('Buku tidak ditemukan!', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        judul = request.form.get('judul', '').strip()
        penulis = request.form.get('penulis', '').strip()
        penerbit = request.form.get('penerbit', '').strip()
        
        if not judul or not penulis or not penerbit:
            flash('Semua field harus diisi!', 'danger')
            return redirect(url_for('edit_book', book_id=book_id))
        
        try:
            conn = get_db()
            conn.execute('UPDATE books SET judul = ?, penulis = ?, penerbit = ? WHERE id = ?', (judul, penulis, penerbit, book_id))
            conn.commit()
            conn.close()
            flash('Buku berhasil diperbarui!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Gagal memperbarui buku: {str(e)}', 'danger')
            return redirect(url_for('edit_book', book_id=book_id))
    
    return render_template('edit.html', book=book)

@app.route('/delete/<book_id>', methods=['POST'])
def delete_book(book_id):
    try:
        conn = get_db()
        conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
        conn.commit()
        conn.close()
        flash('Buku berhasil dihapus!', 'success')
    except Exception as e:
        flash(f'Gagal menghapus buku: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/export')
def preview_export():
    try:
        conn = get_db()
        books = conn.execute('SELECT * FROM books').fetchall()
        conn.close()
        
        if not books:
            flash('Tidak ada data buku untuk diexport!', 'danger')
            return redirect(url_for('index'))
        
        books_list = [dict(b) for b in books]
        sha256_hash = calculate_books_hash(books_list)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(sha256_hash)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        
        return render_template('preview.html', books=books_list, sha256_hash=sha256_hash, qr_base64=qr_base64, timestamp=timestamp)
    except Exception as e:
        flash(f'Gagal memuat preview: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/export/download')
def download_pdf():
    try:
        conn = get_db()
        books = conn.execute('SELECT * FROM books').fetchall()
        conn.close()
        
        books_list = [dict(b) for b in books]
        pdf_buffer = generate_pdf_buffer(books_list)
        
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='data_buku_signed.pdf')
    except Exception as e:
        flash(f'Gagal mendownload PDF: {str(e)}', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
