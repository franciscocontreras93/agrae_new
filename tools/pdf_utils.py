from qgis.PyQt.QtWidgets import QMessageBox  # type: ignore

# --- ReportLab Imports ---
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
# --- End ReportLab Imports ---

# --- Constantes para Tipos de Factura ---
INVOICE_TYPE_ORDINARY = "ordinary"
INVOICE_TYPE_KIT_DIGITAL = "kit_digital"
# --- Fin Constantes ---

def create_invoice_pdf_document(filepath, invoice_data, invoice_type: str = INVOICE_TYPE_ORDINARY, parent_widget=None):
    """
    Generates a PDF invoice document.
    
    :param filepath: Path to save the PDF file.
    :param invoice_data: Dictionary containing all data for the invoice.
                         Expected keys: 'client_name', 'invoice_date_str',
                         'invoice_number_display', 'items' (list of dicts),
                         'subtotal_general_str', 'iva_total_str', 'total_factura_str'.
                         Item dicts expected keys: 'description', 'quantity_str',
                         'unit_price_str', 'vat_str', 'subtotal_str'.
    :param invoice_type: Type of invoice to generate (e.g., INVOICE_TYPE_ORDINARY, INVOICE_TYPE_KIT_DIGITAL).
    :param parent_widget: Parent widget for QMessageBox dialogs.
    :return: True if PDF generation was successful, False otherwise.
    """
    if not REPORTLAB_AVAILABLE:
        QMessageBox.critical(parent_widget, "Error de Dependencia",
                             "La librería ReportLab es necesaria para generar PDFs.\n"
                             "Por favor, instálala (ej: pip install reportlab).")
        return False

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    style_h1 = ParagraphStyle(name='Heading1', fontSize=18, alignment=TA_CENTER, spaceAfter=0.8*cm, fontName='Helvetica-Bold')
    style_body = styles['BodyText']
    style_body_right = ParagraphStyle(name='BodyTextRight', parent=style_body, alignment=TA_RIGHT)
    style_table_header = ParagraphStyle(name='TableHeader', parent=style_body, fontName='Helvetica-Bold', alignment=TA_CENTER)
    style_table_cell = style_body
    style_table_cell_right = ParagraphStyle(name='TableCellRight', parent=style_table_cell, alignment=TA_RIGHT)

    # Título - Varía según el tipo de factura
    if invoice_type == INVOICE_TYPE_KIT_DIGITAL:
        title_text = "FACTURA - PROGRAMA KIT DIGITAL"
        # Podríamos añadir un texto específico para Kit Digital aquí si quisiéramos
        # story.append(Paragraph("Subvencionado por los fondos NextGenerationEU en el marco del Plan de Recuperación, Transformación y Resiliencia.", styles['Italic']))
        # story.append(Spacer(1, 0.3*cm))
    else: # INVOICE_TYPE_ORDINARY o cualquier otro por defecto
        title_text = "FACTURA"
    story.append(Paragraph(title_text, style_h1))
    story.append(Spacer(1, 0.5*cm))

    # Información del Cliente y Factura
    story.append(Paragraph(f"<b>Cliente:</b> {invoice_data.get('client_name', '')}", style_body))
    story.append(Paragraph(f"<b>Fecha Factura:</b> {invoice_data.get('invoice_date_str', '')}", style_body))
    story.append(Paragraph(f"<b>Número Factura:</b> {invoice_data.get('invoice_number_display', '')}", style_body))
    story.append(Spacer(1, 1*cm))

    # Tabla de Ítems
    table_data = [
        [Paragraph("Descripción", style_table_header),
         Paragraph("Cantidad", style_table_header),
         Paragraph("Precio Unit.", style_table_header),
         Paragraph("IVA (%)", style_table_header),
         Paragraph("Subtotal", style_table_header)]
    ]

    for item in invoice_data.get('items', []):
        table_data.append([
            Paragraph(item.get('description', ''), style_table_cell),
            Paragraph(item.get('quantity_str', '0.00'), style_table_cell_right),
            Paragraph(item.get('unit_price_str', '€ 0.00'), style_table_cell_right),
            Paragraph(item.get('vat_str', '0.00%'), style_table_cell_right),
            Paragraph(item.get('subtotal_str', '€ 0.00'), style_table_cell_right)
        ])
    
    col_widths = [doc.width * 0.40, doc.width * 0.15, doc.width * 0.20, doc.width * 0.10, doc.width * 0.15]
    
    item_table = Table(table_data, colWidths=col_widths)
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'), ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10), ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6), ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.black),
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.black),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 1*cm))

    # Totales
    totals_table_data = [
        ["Subtotal General:", invoice_data.get('subtotal_general_str', '€ 0.00')],
        ["IVA Total:", invoice_data.get('iva_total_str', '€ 0.00')],
        [Paragraph("<b>TOTAL:</b>", style_body), Paragraph(f"<b>{invoice_data.get('total_factura_str', '€ 0.00')}</b>", style_body_right)]
    ]
    
    totals_table = Table(totals_table_data, colWidths=[doc.width - 4*cm, 4*cm])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'), ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(totals_table)

    try:
        doc.build(story)
        return True
    except Exception as e:
        QMessageBox.critical(parent_widget, "Error al generar PDF", f"No se pudo generar el archivo PDF:\n{e}")
        print(f"Error detallado al generar PDF: {e}") # Para depuración
        return False
