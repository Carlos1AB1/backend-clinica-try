from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.http import HttpResponse
from io import BytesIO
from datetime import datetime
import os

class PrescriptionPDFGenerator:
    """Generador de PDFs para recetas médicas"""
    
    def __init__(self, prescription):
        self.prescription = prescription
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        self.styles = getSampleStyleSheet()
        self.story = []
        
    def generate_pdf(self):
        """Generar el PDF completo"""
        self._add_header()
        self._add_clinic_info()
        self._add_prescription_info()
        self._add_patient_info()
        self._add_medications_table()
        self._add_instructions()
        self._add_footer()
        
        self.doc.build(self.story)
        self.buffer.seek(0)
        return self.buffer

    def _add_header(self):
        """Agregar encabezado del documento"""
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        title = Paragraph("RECETA MÉDICA VETERINARIA", title_style)
        self.story.append(title)
        self.story.append(Spacer(1, 20))

    def _add_clinic_info(self):
        """Agregar información de la clínica"""
        clinic_style = ParagraphStyle(
            'ClinicInfo',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        clinic_info = f"""
        <b>{settings.CLINIC_NAME}</b><br/>
        {settings.CLINIC_ADDRESS}<br/>
        Tel: {settings.CLINIC_PHONE} | Email: {settings.CLINIC_EMAIL}
        """
        
        clinic_para = Paragraph(clinic_info, clinic_style)
        self.story.append(clinic_para)
        self.story.append(Spacer(1, 20))

    def _add_prescription_info(self):
        """Agregar información de la receta"""
        info_data = [
            ['Número de Receta:', self.prescription.prescription_number],
            ['Fecha de Emisión:', self.prescription.issue_date.strftime('%d/%m/%Y %H:%M')],
            ['Fecha de Vencimiento:', self.prescription.expiration_date.strftime('%d/%m/%Y')],
            ['Estado:', self.prescription.get_status_display()],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.story.append(info_table)
        self.story.append(Spacer(1, 20))

    def _add_patient_info(self):
        """Agregar información del paciente"""
        patient_style = ParagraphStyle(
            'PatientInfo',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10
        )
        
        # Aquí normalmente harías una llamada al microservicio de usuarios
        # Por simplicidad, usamos los IDs
        patient_info = f"""
        <b>INFORMACIÓN DEL PACIENTE</b><br/>
        ID Paciente: {self.prescription.patient_id}<br/>
        ID Propietario: {self.prescription.owner_id}<br/>
        ID Veterinario: {self.prescription.veterinarian_id}<br/>
        Cédula Veterinario: {self.prescription.veterinarian_license}
        """
        
        patient_para = Paragraph(patient_info, patient_style)
        self.story.append(patient_para)
        self.story.append(Spacer(1, 15))

    def _add_medications_table(self):
        """Agregar tabla de medicamentos"""
        # Encabezado de la tabla
        header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.darkblue
        )
        
        medications_title = Paragraph("<b>MEDICAMENTOS PRESCRITOS</b>", header_style)
        self.story.append(medications_title)
        self.story.append(Spacer(1, 10))
        
        # Datos de la tabla
        table_data = [
            ['Medicamento', 'Concentración', 'Cantidad', 'Dosis', 'Frecuencia', 'Duración']
        ]
        
        for item in self.prescription.items.all():
            table_data.append([
                item.medication.name,
                item.medication.concentration,
                str(item.quantity_prescribed),
                item.dosage,
                item.frequency,
                item.duration
            ])
        
        medications_table = Table(table_data, colWidths=[
            1.5*inch, 1*inch, 0.8*inch, 1*inch, 1*inch, 1*inch
        ])
        
        medications_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ]))
        
        self.story.append(medications_table)
        self.story.append(Spacer(1, 20))

    def _add_instructions(self):
        """Agregar instrucciones y diagnóstico"""
        instructions_style = ParagraphStyle(
            'Instructions',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leftIndent=20
        )
        
        # Diagnóstico
        if self.prescription.diagnosis:
            diagnosis_title = Paragraph("<b>DIAGNÓSTICO:</b>", self.styles['Heading3'])
            self.story.append(diagnosis_title)
            diagnosis_text = Paragraph(self.prescription.diagnosis, instructions_style)
            self.story.append(diagnosis_text)
            self.story.append(Spacer(1, 10))
        
        # Instrucciones especiales
        if self.prescription.special_instructions:
            instructions_title = Paragraph("<b>INSTRUCCIONES ESPECIALES:</b>", self.styles['Heading3'])
            self.story.append(instructions_title)
            instructions_text = Paragraph(self.prescription.special_instructions, instructions_style)
            self.story.append(instructions_text)
            self.story.append(Spacer(1, 10))
        
        # Instrucciones por medicamento
        for item in self.prescription.items.all():
            if item.special_instructions:
                med_title = Paragraph(f"<b>{item.medication.name}:</b>", self.styles['Heading4'])
                self.story.append(med_title)
                med_instructions = Paragraph(item.special_instructions, instructions_style)
                self.story.append(med_instructions)
                
                if item.with_food:
                    food_note = Paragraph("• <b>Administrar con alimento</b>", instructions_style)
                    self.story.append(food_note)
                
                self.story.append(Spacer(1, 10))

    def _add_footer(self):
        """Agregar pie de página"""
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        self.story.append(Spacer(1, 30))
        
        # Línea para firma
        signature_line = "_" * 50
        signature_text = f"""
        <br/>
        <br/>
        {signature_line}<br/>
        <b>Firma del Veterinario</b><br/>
        Cédula: {self.prescription.veterinarian_license}
        """
        
        signature_para = Paragraph(signature_text, footer_style)
        self.story.append(signature_para)
        
        # Información legal
        legal_text = f"""
        <br/>
        <br/>
        <i>Esta receta es válida hasta el {self.prescription.expiration_date.strftime('%d/%m/%Y')}.<br/>
        No se aceptan alteraciones. Conserve este documento.</i>
        """
        
        legal_para = Paragraph(legal_text, footer_style)
        self.story.append(legal_para)

def generate_prescription_pdf_response(prescription):
    """Generar respuesta HTTP con PDF de la receta"""
    generator = PrescriptionPDFGenerator(prescription)
    pdf_buffer = generator.generate_pdf()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receta_{prescription.prescription_number}.pdf"'
    response.write(pdf_buffer.getvalue())
    
    return response

def generate_prescription_pdf_file(prescription, save_path=None):
    """Generar archivo PDF de la receta"""
    generator = PrescriptionPDFGenerator(prescription)
    pdf_buffer = generator.generate_pdf()
    
    if save_path:
        with open(save_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        return save_path
    
    return pdf_buffer.getvalue() 