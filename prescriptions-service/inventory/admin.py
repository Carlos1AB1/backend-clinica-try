from django.contrib import admin
from .models import MedicationCategory, Medication, StockMovement

@admin.register(MedicationCategory)
class MedicationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_stock', 'unit_price', 'requires_prescription', 'is_active']
    list_filter = ['category', 'requires_prescription', 'prescription_type', 'medication_type', 'is_active']
    search_fields = ['name', 'generic_name', 'active_ingredient']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['medication', 'movement_type', 'quantity', 'stock_after', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['medication__name', 'reference_document'] 