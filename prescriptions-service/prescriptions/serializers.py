from rest_framework import serializers
from django.db import transaction
from datetime import date, timedelta
from .models import Prescription, PrescriptionItem, PrescriptionDispensation, PrescriptionDispensationItem
from inventory.models import Medication, StockMovement

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    medication_concentration = serializers.CharField(source='medication.concentration', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining_quantity = serializers.ReadOnlyField()
    is_fully_dispensed = serializers.ReadOnlyField()
    
    class Meta:
        model = PrescriptionItem
        fields = '__all__'
        read_only_fields = ('total_price',)

    def validate(self, data):
        medication = data.get('medication')
        quantity_prescribed = data.get('quantity_prescribed')
        
        # Validar que el medicamento esté activo
        if medication and not medication.is_active:
            raise serializers.ValidationError({
                'medication': 'El medicamento seleccionado no está activo'
            })
        
        # Validar que el medicamento requiera receta si es necesario
        if medication and medication.prescription_type == 'CONTROLADO':
            user = self.context['request'].user
            if user.get('role') != 'Veterinario':
                raise serializers.ValidationError({
                    'medication': 'Solo los veterinarios pueden prescribir medicamentos controlados'
                })
        
        # Validar disponibilidad en inventario
        if medication and quantity_prescribed:
            if medication.current_stock < quantity_prescribed:
                raise serializers.ValidationError({
                    'quantity_prescribed': f'Stock insuficiente. Disponible: {medication.current_stock}'
                })
        
        return data

    def create(self, validated_data):
        # Establecer el precio unitario actual del medicamento
        medication = validated_data['medication']
        validated_data['unit_price'] = medication.unit_price
        return super().create(validated_data)

class PrescriptionListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    patient_name = serializers.CharField(read_only=True)
    owner_name = serializers.CharField(read_only=True)
    veterinarian_name = serializers.CharField(read_only=True)
    is_expired = serializers.ReadOnlyField()
    can_be_dispensed = serializers.ReadOnlyField()
    
    class Meta:
        model = Prescription
        fields = (
            'id', 'prescription_number', 'patient_id', 'patient_name', 
            'owner_name', 'veterinarian_name', 'diagnosis', 'status', 
            'status_display', 'issue_date', 'expiration_date', 'total_amount',
            'items_count', 'is_expired', 'can_be_dispensed', 'dispensation_count'
        )

    def get_items_count(self, obj):
        return obj.items.count()

class PrescriptionDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(read_only=True)
    owner_name = serializers.CharField(read_only=True)
    veterinarian_name = serializers.CharField(read_only=True)
    is_expired = serializers.ReadOnlyField()
    can_be_dispensed = serializers.ReadOnlyField()
    dispensation_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ('prescription_number', 'issue_date', 'total_amount', 'dispensed_date')

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True)
    
    class Meta:
        model = Prescription
        fields = (
            'patient_id', 'owner_id', 'consultation_id', 'diagnosis', 'symptoms',
            'treatment_notes', 'expiration_date', 'veterinarian_license',
            'special_instructions', 'follow_up_required', 'follow_up_date',
            'can_be_dispensed_multiple_times', 'max_dispensations', 'items'
        )

    def validate(self, data):
        # Validar que haya al menos un medicamento
        items = data.get('items', [])
        if not items:
            raise serializers.ValidationError({
                'items': 'Debe incluir al menos un medicamento en la receta'
            })
        
        # Validar fecha de vencimiento
        expiration_date = data.get('expiration_date')
        if expiration_date and expiration_date <= date.today():
            raise serializers.ValidationError({
                'expiration_date': 'La fecha de vencimiento debe ser futura'
            })
        
        # Validar fecha de seguimiento
        follow_up_date = data.get('follow_up_date')
        follow_up_required = data.get('follow_up_required', False)
        
        if follow_up_required and not follow_up_date:
            raise serializers.ValidationError({
                'follow_up_date': 'Si requiere seguimiento, debe especificar la fecha'
            })
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Asignar veterinario automáticamente
        validated_data['veterinarian_id'] = self.context['request'].user.get('id')
        
        # Establecer fecha de vencimiento por defecto (30 días)
        if not validated_data.get('expiration_date'):
            validated_data['expiration_date'] = date.today() + timedelta(days=30)
        
        prescription = Prescription.objects.create(**validated_data)
        
        total_amount = 0
        
        # Crear items de la receta
        for item_data in items_data:
            item_data['prescription'] = prescription
            item_serializer = PrescriptionItemSerializer(data=item_data, context=self.context)
            item_serializer.is_valid(raise_exception=True)
            item = item_serializer.save()
            total_amount += item.total_price
        
        # Actualizar monto total
        prescription.total_amount = total_amount
        prescription.save()
        
        return prescription

class PrescriptionDispensationItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='prescription_item.medication.name', read_only=True)
    
    class Meta:
        model = PrescriptionDispensationItem
        fields = '__all__'
        read_only_fields = ('total_price',)

class PrescriptionDispensationSerializer(serializers.ModelSerializer):
    items = PrescriptionDispensationItemSerializer(many=True)
    prescription_number = serializers.CharField(source='prescription.prescription_number', read_only=True)
    
    class Meta:
        model = PrescriptionDispensation
        fields = '__all__'
        read_only_fields = ('dispensation_date', 'dispensed_by', 'total_amount')

    def validate(self, data):
        prescription = data.get('prescription')
        items = data.get('items', [])
        
        # Validar que la receta pueda ser dispensada
        if prescription and not prescription.can_be_dispensed:
            raise serializers.ValidationError({
                'prescription': 'Esta receta no puede ser dispensada'
            })
        
        # Validar que haya items para dispensar
        if not items:
            raise serializers.ValidationError({
                'items': 'Debe especificar al menos un medicamento para dispensar'
            })
        
        # Validar disponibilidad de cada medicamento
        for item_data in items:
            prescription_item = item_data.get('prescription_item')
            quantity_to_dispense = item_data.get('quantity_dispensed')
            
            if prescription_item:
                # Verificar que no se exceda la cantidad prescrita
                remaining = prescription_item.remaining_quantity
                if quantity_to_dispense > remaining:
                    raise serializers.ValidationError({
                        'items': f'No se puede dispensar más de {remaining} unidades de {prescription_item.medication.name}'
                    })
                
                # Verificar stock disponible
                medication = prescription_item.medication
                if medication.current_stock < quantity_to_dispense:
                    raise serializers.ValidationError({
                        'items': f'Stock insuficiente de {medication.name}. Disponible: {medication.current_stock}'
                    })
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Asignar usuario que dispensa
        validated_data['dispensed_by'] = self.context['request'].user.get('id')
        
        dispensation = PrescriptionDispensation.objects.create(**validated_data)
        
        total_amount = 0
        
        for item_data in items_data:
            prescription_item = item_data['prescription_item']
            quantity_dispensed = item_data['quantity_dispensed']
            
            # Crear item de dispensación
            item_data['dispensation'] = dispensation
            item_data['unit_price'] = prescription_item.medication.unit_price
            
            dispensation_item = PrescriptionDispensationItem.objects.create(**item_data)
            total_amount += dispensation_item.total_price
            
            # Actualizar cantidad dispensada en el item de receta
            prescription_item.quantity_dispensed += quantity_dispensed
            prescription_item.save()
            
            # Crear movimiento de stock
            medication = prescription_item.medication
            StockMovement.objects.create(
                medication=medication,
                movement_type='VENTA',
                quantity=-quantity_dispensed,  # Negativo porque es salida
                unit_cost=medication.unit_price,
                prescription_id=dispensation.prescription.id,
                stock_after=medication.current_stock - quantity_dispensed,
                reason=f'Dispensación receta {dispensation.prescription.prescription_number}',
                created_by=self.context['request'].user.get('id')
            )
            
            # Actualizar stock del medicamento
            medication.current_stock -= quantity_dispensed
            medication.save()
        
        # Actualizar totales de la dispensación
        dispensation.total_amount = total_amount
        dispensation.save()
        
        # Actualizar estado de la receta
        prescription = dispensation.prescription
        prescription.dispensation_count += 1
        
        # Verificar si todos los items están completamente dispensados
        all_dispensed = all(item.is_fully_dispensed for item in prescription.items.all())
        
        if all_dispensed:
            prescription.status = 'DISPENSADA'
            prescription.dispensed_date = dispensation.dispensation_date
        else:
            prescription.status = 'PARCIAL'
        
        prescription.save()
        
        return dispensation 