from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from datetime import datetime
from config import CLINIC_NAME, CLINIC_PHONE, CLINIC_TELEGRAM, DISCLAIMER

def generate_pdf(user_id, name, answers, rec):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    story = []
    story.append(Paragraph(f"{CLINIC_NAME}", styles['Title']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Клиент: {name}", styles['Normal']))
    story.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Рекомендуемые процедуры:", styles['Heading2']))
    for p in rec['procedures']:
        story.append(Paragraph(f"• {p['name']} - {p['price']}", styles['Normal']))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Домашний уход:", styles['Heading2']))
    for h in rec['homecare']:
        story.append(Paragraph(f"• {h['name']} - {h['how_to_use']}", styles['Normal']))
    
    if rec['warnings']:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Важно:", styles['Heading2']))
        for w in rec['warnings']:
            story.append(Paragraph(f"⚠️ {w}", styles['Normal']))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Запись: {CLINIC_PHONE} или {CLINIC_TELEGRAM}", styles['Normal']))
    story.append(Paragraph(DISCLAIMER, styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer