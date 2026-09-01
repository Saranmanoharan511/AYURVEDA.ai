"""
PDF Generation Service

This module provides functionality to generate prescription PDFs using ReportLab.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from typing import List, Dict


class PDFService:
    """Service for generating prescription PDFs."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#008080'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#444444'),
            spaceAfter=10
        ))
    
    def generate_prescription_pdf(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        doctor_qualifications: str,
        consultation_id: str,
        consultation_date: str,
        prescriptions: List[Dict]
    ) -> BytesIO:
        """
        Generate a prescription PDF.
        
        Args:
            patient_name: Patient's full name
            patient_email: Patient's email
            doctor_name: Doctor's name
            doctor_qualifications: Doctor's qualifications
            consultation_id: Consultation ID
            consultation_date: Consultation scheduled date
            prescriptions: List of prescription dictionaries with keys:
                - name: Medicine name
                - morning_dosage: Morning dosage (0-3)
                - afternoon_dosage: Afternoon dosage (0-3)
                - night_dosage: Night dosage (0-3)
                - food_timing: 'before_food' or 'after_food'
                - notes: Additional notes
        
        Returns:
            BytesIO object containing the PDF data
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("Ayurveda Prescription", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Patient and Doctor Information
        info_data = [
            ['Patient Information', ''],
            ['Name:', patient_name],
            ['Email:', patient_email],
            ['', ''],
            ['Doctor Information', ''],
            ['Name:', doctor_name],
            ['Qualifications:', doctor_qualifications],
            ['', ''],
            ['Consultation Details', ''],
            ['Consultation ID:', consultation_id],
            ['Date:', consultation_date]
        ]
        
        info_table = Table(info_data, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 0), (0, -1), [colors.HexColor('#F0F0F0')]),
            ('ROWBACKGROUNDS', (0, 4), (4, -1), [colors.HexColor('#F0F0F0')]),
            ('ROWBACKGROUNDS', (0, 8), (8, -1), [colors.HexColor('#F0F0F0')]),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Prescriptions Table
        elements.append(Paragraph("Prescribed Medicines", self.styles['CustomHeading']))
        
        if prescriptions:
            # Table header
            table_data = [
                ['#', 'Medicine Name', 'Morning', 'Afternoon', 'Night', 'Food Timing', 'Notes']
            ]
            
            # Table rows
            for idx, prescription in enumerate(prescriptions, 1):
                food_timing_display = 'Before Food' if prescription.get('food_timing') == 'before_food' else 'After Food'
                row = [
                    str(idx),
                    prescription.get('name', ''),
                    str(prescription.get('morning_dosage', 0)),
                    str(prescription.get('afternoon_dosage', 0)),
                    str(prescription.get('night_dosage', 0)),
                    food_timing_display,
                    prescription.get('notes', '')
                ]
                table_data.append(row)
            
            prescription_table = Table(table_data, colWidths=[0.5 * inch, 2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.2 * inch, 1.5 * inch])
            prescription_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#008080')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            
            elements.append(prescription_table)
        else:
            elements.append(Paragraph("No prescriptions added.", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 0.5 * inch))
        
        # Footer
        footer_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elements.append(Paragraph(footer_text, self.styles['CustomBody']))
        
        # Build PDF
        doc.build(elements)
        
        # Reset buffer position
        buffer.seek(0)
        
        return buffer


# Global instance
pdf_service = PDFService()
