import hashlib
import json
import time
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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

def generate_pdf_buffer(books):
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
    story.append(Spacer(1, 30))
    
    sha256_hash = calculate_books_hash(books)
    
    section_title_style = ParagraphStyle('SectionTitle', fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#1e293b'), spaceAfter=8)
    hash_style = ParagraphStyle('HashStyle', fontName='Courier', fontSize=9, textColor=colors.HexColor('#475569'), spaceAfter=15)
    
    story.append(Paragraph("Tanda Tangan Digital", section_title_style))
    story.append(Paragraph(f"Message Digest (SHA-256):<br/><b>{sha256_hash}</b>", hash_style))
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=0)
    qr.add_data(sha256_hash)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    rl_qr_img = Image(qr_buffer, width=100, height=100)
    rl_qr_img.hAlign = 'LEFT'
    story.append(rl_qr_img)
    story.append(Spacer(1, 20))
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    footer_style = ParagraphStyle('FooterStyle', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.HexColor('#94a3b8'), spaceAfter=10)
    story.append(Paragraph(f"Dokumen ini dibuat otomatis pada: {timestamp}", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
