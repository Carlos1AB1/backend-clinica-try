from django.contrib import admin
from .models import MedicationCategory, Medication, InventoryMovement

@admin.register(MedicationCategory)
class MedicationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'current_stock', 'unit_price', 'requires_prescription']
    list_filter = ['category', 'requires_prescription']
    search_fields = ['name', 'active_ingredient']

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['medication', 'movement_type', 'quantity', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['medication__name'] 