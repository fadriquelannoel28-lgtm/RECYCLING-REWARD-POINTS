import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from db import get_db

def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
    canvas.setLineWidth(0.5)
    canvas.line(40, 42, 555.27, 42)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.drawString(40, 28, 'EcoCoins • Barangay Pinagkawitan, Lipa City')
    canvas.drawRightString(555.27, 28, 'Page 1')
    canvas.restoreState()

def _get_styles():
    base = getSampleStyleSheet()['Normal']
    return {
        'title_left': ParagraphStyle('HLeft', parent=base, fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#0d462b')),
        'badge_right': ParagraphStyle('BRight', parent=base, fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=TA_RIGHT, textColor=colors.HexColor('#198754')),
        'h1': ParagraphStyle('DH1', parent=base, fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#0d462b')),
        'sub': ParagraphStyle('DSub', parent=base, fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#64748b')),
        'meta_label': ParagraphStyle('MLabel', parent=base, fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#475569')),
        'meta_val': ParagraphStyle('MVal', parent=base, fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#0f172a')),
        'sec_title': ParagraphStyle('STitle', parent=base, fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#0d462b')),
        'th_left': ParagraphStyle('THL', parent=base, fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=colors.HexColor('#0d462b')),
        'th_right': ParagraphStyle('THR', parent=base, fontName='Helvetica-Bold', fontSize=9.5, leading=12, alignment=TA_RIGHT, textColor=colors.HexColor('#0d462b')),
        'td_left': ParagraphStyle('TDL', parent=base, fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor('#1e293b')),
        'td_right': ParagraphStyle('TDR', parent=base, fontName='Helvetica-Bold', fontSize=9.5, leading=13, alignment=TA_RIGHT, textColor=colors.HexColor('#1e293b')),
        'td_right_pts': ParagraphStyle('TDRP', parent=base, fontName='Helvetica-Bold', fontSize=9.5, leading=13, alignment=TA_RIGHT, textColor=colors.HexColor('#198754')),
        'sig_text': ParagraphStyle('SText', parent=base, fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#334155')),
    }

def generate_participation_report_pdf():
    conn = get_db()
    cur = conn.cursor()
    all_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions").fetchall()]
    residents_list = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'resident'").fetchall()]
    staff_list = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'staff'").fetchall()]
    all_redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions").fetchall()]
    conn.close()

    total_points = sum(int(t.get('points_earned', 0)) for t in all_txs)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=36, bottomMargin=48)
    st = _get_styles()

    story = []

    header_table = Table([[Paragraph('<font color="#0d462b">&#9632;</font>  EcoCoins', st['title_left']), Paragraph('BARANGAY ENVIRONMENTAL REPORT', st['badge_right'])]], colWidths=[315.27, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 22))

    story.append(Paragraph('Barangay Recycling Reports', st['h1']))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Official summary report for barangay environmental compliance.', st['sub']))
    story.append(Spacer(1, 16))

    now = datetime.now()
    now_date = f"{now.strftime('%B')} {now.day}, {now.year}"

    meta_cells = [
        [
            [Paragraph('Barangay', st['meta_label']), Paragraph('Pinagkawitan, Lipa City', st['meta_val'])],
            [Paragraph('Report generated', st['meta_label']), Paragraph(now_date, st['meta_val'])],
            [Paragraph('Report type', st['meta_label']), Paragraph('Summary', st['meta_val'])],
        ],
        [
            [Paragraph('Reporting period', st['meta_label']), Paragraph('All recorded transactions', st['meta_val'])],
            [Paragraph('Prepared by', st['meta_label']), Paragraph('EcoCoins Administrator', st['meta_val'])],
            [Paragraph('Document', st['meta_label']), Paragraph('EC-RPT-001', st['meta_val'])],
        ]
    ]
    t_meta = Table(meta_cells, colWidths=[171.75, 171.75, 171.75])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 24))

    story.append(Paragraph('1. Community Participation Report', st['sec_title']))
    story.append(Spacer(1, 10))

    table_rows = [
        [Paragraph('Metric', st['th_left']), Paragraph('Recorded total', st['th_right'])],
        [Paragraph('Registered Residents', st['td_left']), Paragraph(str(len(residents_list)), st['td_right'])],
        [Paragraph('Active Collection Staff', st['td_left']), Paragraph(str(len(staff_list)), st['td_right'])],
        [Paragraph('Total Deposits Recorded', st['td_left']), Paragraph(str(len(all_txs)), st['td_right'])],
        [Paragraph('Total Points Issued', st['td_left']), Paragraph(f'{total_points:,} pts', st['td_right_pts'])],
        [Paragraph('Total Rewards Claimed', st['td_left']), Paragraph(str(len(all_redemptions)), st['td_right'])],
    ]
    t_data = Table(table_rows, colWidths=[365.27, 150])
    t_data.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d1e7dd')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(t_data)
    story.append(Spacer(1, 50))

    sig_data = [
        [Paragraph('Prepared by:', st['sig_text']), '', Paragraph('Reviewed / Approved by:', st['sig_text'])],
        ['', '', ''],
        [Paragraph('____________________________', st['sig_text']), '', Paragraph('____________________________', st['sig_text'])],
        [Paragraph('EcoCoins Administrator', st['sig_text']), '', Paragraph('Barangay Authorized Representative', st['sig_text'])],
    ]
    t_sig = Table(sig_data, colWidths=[230, 55.27, 230], rowHeights=[14, 30, 14, 14])
    t_sig.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_sig)

    doc.build(story, onFirstPage=_draw_footer)
    return buf.getvalue()

def generate_materials_report_pdf():
    conn = get_db()
    cur = conn.cursor()
    all_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions").fetchall()]
    conn.close()

    mat_counts = {'Plastic Bottles': 0, 'Aluminum Cans': 0, 'Other Recyclables': 0}
    for t in all_txs:
        m_name = str(t.get('material_name', '')).lower()
        q = int(t.get('quantity', 0))
        if 'bottle' in m_name or 'plastic' in m_name:
            mat_counts['Plastic Bottles'] += q
        elif 'can' in m_name:
            mat_counts['Aluminum Cans'] += q
        else:
            mat_counts['Other Recyclables'] += q

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=36, bottomMargin=48)
    st = _get_styles()

    story = []

    header_table = Table([[Paragraph('<font color="#0d462b">&#9632;</font>  EcoCoins', st['title_left']), Paragraph('BARANGAY ENVIRONMENTAL REPORT', st['badge_right'])]], colWidths=[315.27, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 22))

    story.append(Paragraph('Barangay Recycling Reports', st['h1']))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Official summary report for barangay environmental compliance.', st['sub']))
    story.append(Spacer(1, 16))

    now = datetime.now()
    now_date = f"{now.strftime('%B')} {now.day}, {now.year}"

    meta_cells = [
        [
            [Paragraph('Barangay', st['meta_label']), Paragraph('Pinagkawitan, Lipa City', st['meta_val'])],
            [Paragraph('Report generated', st['meta_label']), Paragraph(now_date, st['meta_val'])],
            [Paragraph('Report type', st['meta_label']), Paragraph('Summary', st['meta_val'])],
        ],
        [
            [Paragraph('Reporting period', st['meta_label']), Paragraph('All recorded transactions', st['meta_val'])],
            [Paragraph('Prepared by', st['meta_label']), Paragraph('EcoCoins Administrator', st['meta_val'])],
            [Paragraph('Document', st['meta_label']), Paragraph('EC-RPT-002', st['meta_val'])],
        ]
    ]
    t_meta = Table(meta_cells, colWidths=[171.75, 171.75, 171.75])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 24))

    story.append(Paragraph('1. Collected Materials Summary', st['sec_title']))
    story.append(Spacer(1, 10))

    table_rows = [
        [Paragraph('Material category', st['th_left']), Paragraph('Collected quantity', st['th_right'])],
        [Paragraph('Plastic Bottles', st['td_left']), Paragraph(f"{mat_counts['Plastic Bottles']} pcs", st['td_right'])],
        [Paragraph('Aluminum Cans', st['td_left']), Paragraph(f"{mat_counts['Aluminum Cans']} pcs", st['td_right'])],
        [Paragraph('Other Recyclables', st['td_left']), Paragraph(f"{mat_counts['Other Recyclables']} pcs/kg", st['td_right'])],
    ]
    t_data = Table(table_rows, colWidths=[365.27, 150])
    t_data.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d1e7dd')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(t_data)
    story.append(Spacer(1, 50))

    sig_data = [
        [Paragraph('Prepared by:', st['sig_text']), '', Paragraph('Reviewed / Approved by:', st['sig_text'])],
        ['', '', ''],
        [Paragraph('____________________________', st['sig_text']), '', Paragraph('____________________________', st['sig_text'])],
        [Paragraph('EcoCoins Administrator', st['sig_text']), '', Paragraph('Barangay Authorized Representative', st['sig_text'])],
    ]
    t_sig = Table(sig_data, colWidths=[230, 55.27, 230], rowHeights=[14, 30, 14, 14])
    t_sig.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_sig)

    doc.build(story, onFirstPage=_draw_footer)
    return buf.getvalue()
