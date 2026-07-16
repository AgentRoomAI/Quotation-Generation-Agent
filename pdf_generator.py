import os
from datetime import datetime
from typing import List, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle


class QuotationPDFGenerator:
    """Generate a professional quotation PDF using ReportLab."""

    company_name = "Quotation Agent"
    company_tagline = "B2B Sales Desk "
    company_address = "AI-Powered Business Quotation"
    company_contact = "support@example.com"

    def __init__(self, output_dir: str = "pdfs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _build_header(self, styles, quotation_id: str, customer_name: str):
        title_style = ParagraphStyle(
            name="QuoteTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1F3B5B"),
            fontSize=22,
            leading=26,
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            name="QuoteSubtitle",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#5A6B7A"),
            fontSize=10,
            leading=12,
        )

        header_data = [[
            Paragraph(f"<b>{self.company_name}</b>", styles["Heading1"]),
            Paragraph(
                f"<b>Quotation ID:</b> {quotation_id}<br/><b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}",
                styles["BodyText"],
            ),
        ]]
        header_table = Table(header_data, colWidths=[4.7 * inch, 2.8 * inch])
        header_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F7FB")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#D5DEE8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D5DEE8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 10),
            ])
        )

        return [
            Paragraph(self.company_name, title_style),
            Paragraph(self.company_tagline, subtitle_style),
            Spacer(1, 0.12 * inch),
            header_table,
            Spacer(1, 0.15 * inch),
            Paragraph(f"<b>Customer name:</b> {customer_name}", styles["Heading4"]),
            Paragraph("This quotation is valid for 30 days from the date of issue.", styles["BodyText"]),
            Spacer(1, 0.15 * inch),
        ]

    def _build_footer(self, canvas, doc):
        canvas.saveState()
        width, height = letter
        canvas.setStrokeColor(colors.HexColor("#D5DEE8"))
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, 0.75 * inch, width - doc.rightMargin, 0.75 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6B7785"))
        canvas.drawString(doc.leftMargin, 0.55 * inch, self.company_address)
        canvas.drawRightString(width - doc.rightMargin, 0.55 * inch, f"Contact: {self.company_contact}")
        canvas.drawCentredString(width / 2.0, 0.35 * inch, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    def generate(self, quotation_data: Dict[str, Any], customer_name: str, quotation_id: str) -> str:
        filename = f"{quotation_id}.pdf"
        full_path = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(
            full_path,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.8 * inch,
            bottomMargin=1.0 * inch,
        )
        styles = getSampleStyleSheet()
        right_style = ParagraphStyle(name="RightBody", parent=styles["BodyText"], alignment=TA_RIGHT)
        center_style = ParagraphStyle(name="CenterBody", parent=styles["BodyText"], alignment=TA_CENTER)
        story = []

        story.extend(self._build_header(styles, quotation_id, customer_name))

        data = [["Product", "Qty", "Unit Price", "GST", "Line Total"]]
        for item in quotation_data.get("items", []):
            line_total = (item["quantity"] * item["unit_price"]) * (1 + (item["gst"] / 100))
            data.append([
                item["product_name"],
                str(item["quantity"]),
                f"₹{item['unit_price']:,.2f}",
                f"{item['gst']}%",
                f"₹{line_total:,.2f}",
            ])

        table = Table(data, repeatRows=1, colWidths=[3.0 * inch, 0.6 * inch, 1.1 * inch, 0.7 * inch, 1.3 * inch])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3B5B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBFD")]),
                ("PADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 0.22 * inch))

        totals_data = [
            [Paragraph("Subtotal", styles["BodyText"]), Paragraph(f"₹{quotation_data['subtotal']:,.2f}", right_style)],
            [Paragraph("GST", styles["BodyText"]), Paragraph(f"₹{quotation_data['gst_total']:,.2f}", right_style)],
            [Paragraph("Shipping", styles["BodyText"]), Paragraph(f"₹{quotation_data['shipping']:,.2f}", right_style)],
            [Paragraph("Grand Total", styles["Heading4"]), Paragraph(f"₹{quotation_data['grand_total']:,.2f}", ParagraphStyle(name="GrandTotal", parent=styles["Heading4"], alignment=TA_RIGHT, textColor=colors.HexColor("#1F3B5B")))],
        ]
        totals_table = Table(totals_data, colWidths=[5.5 * inch, 1.6 * inch])
        totals_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F7FB")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D5DEE8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DEE8")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
        story.append(totals_table)
        story.append(Spacer(1, 0.18 * inch))

        terms_title = ParagraphStyle(name="TermsTitle", parent=styles["Heading4"], textColor=colors.HexColor("#1F3B5B"))
        story.append(Paragraph("Terms & Conditions", terms_title))
        story.append(Paragraph("Prices are subject to change without notice. Payment is due within 30 days. This quotation is valid for 30 days from the issue date.", styles["BodyText"]))
        story.append(Spacer(1, 0.08 * inch))
        story.append(Paragraph("Thank you for choosing us for your business requirements.", center_style))

        doc.build(story, onFirstPage=self._build_footer, onLaterPages=self._build_footer)
        return full_path
