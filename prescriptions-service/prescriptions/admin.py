from django.contrib import admin
from .models import Prescription, PrescriptionItem, PrescriptionDispensation

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['prescription_number', 'patient_id', 'veterinarian_id', 'issue_date', 'status']
    list_filter = ['status', 'issue_date', 'expiration_date']
    search_fields = ['prescription_number', 'patient_id', 'veterinarian_id']

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'medication', 'quantity_prescribed', 'dosage']
    search_fields = ['prescription__prescription_number', 'medication__name']

@admin.register(PrescriptionDispensation)
class PrescriptionDispensationAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'dispensation_date', 'dispensed_by', 'total_amount']
    list_filter = ['dispensation_date']
    search_fields = ['prescription__prescription_number'] 