import hashlib
import json
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table as RTTable
import qrcode

def calculate_books_hash(books):
    books_data = []
    for b in books:
        books_data.append({
            'id': b['id'],
            'judul': b['judul'],
            'penulis': b['penulis'],
            'penerbit': b['penerbit']
        })
    books_data.sort(key=lambda x: x['id'])
    serialized = json.dumps(books_data, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def generate_pdf_buffer(books, verify_url=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=24, textColor=colors.HexColor('#1e293b'), spaceAfter=20)
    story.append(Paragraph("Data Buku", title_style))
    story.append(Spacer(1, 10))
    
    data = [["Judul", "Penulis", "Penerbit"]]
    for b in books:
        data.append([b['judul'], b['penulis'], b['penerbit']])
    
    t = Table(data, colWidths=[200, 160, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.HexColor('#334155')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ('TOPPADDING', (0,1), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 60))
    
    sha256_hash = calculate_books_hash(books)
    
    # =========================================================
    # QR CODE DI SEBELAH KANAN
    # =========================================================
    
    qr_buffer = BytesIO()
    
    # PERBAIKAN: Jangan gunakan domain fiktif!
    # Jika verify_url tidak dikirim, buat URL default yang valid
    if not verify_url:
        # Gunakan localhost atau alamat IP Anda
        verify_url = "http://127.0.0.1:5000/verify/token_example"
    
    qr = qrcode.QRCode(
        version=5,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=25,
        border=8
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    qr_img_reportlab = Image(qr_buffer, width=160, height=160)
    
    # Style untuk teks (rata kanan)
    jabatan_style = ParagraphStyle('Jabatan', fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#64748b'), alignment=2)
    nama_style = ParagraphStyle('Nama', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#1e293b'), alignment=2)
    
    ttd_content = [
        Paragraph("CEO LibSigManager", jabatan_style),
        Spacer(1, 8),
        qr_img_reportlab,
        Spacer(1, 8),
        Paragraph("Ahmad Zamroni", nama_style)
    ]
    
    ttd_table = RTTable([
        [ttd_content]
    ], colWidths=[180])
    ttd_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(ttd_table)
    story.append(Spacer(1, 20))
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    footer_style = ParagraphStyle('FooterStyle', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#94a3b8'), spaceAfter=10, alignment=1)
    story.append(Paragraph(f"Dokumen ini dibuat otomatis pada: {timestamp}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer