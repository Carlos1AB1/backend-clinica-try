from rest_framework import serializers
from .models import MedicationCategory, Medication, StockMovement

class MedicationCategorySerializer(serializers.ModelSerializer):
    medications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicationCategory
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_medications_count(self, obj):
        return obj.medication_set.filter(is_active=True).count()

class MedicationListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    medication_type_display = serializers.CharField(source='get_medication_type_display', read_only=True)
    prescription_type_display = serializers.CharField(source='get_prescription_type_display', read_only=True)
    stock_status = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Medication
        fields = (
            'id', 'name', 'generic_name', 'category_name', 'active_ingredient',
            'concentration', 'medication_type', 'medication_type_display',
            'prescription_type', 'prescription_type_display', 'manufacturer',
            'unit_price', 'current_stock', 'minimum_stock', 'stock_status',
            'is_low_stock', 'is_expired', 'expiration_date', 'is_active'
        )

class MedicationDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    medication_type_display = serializers.CharField(source='get_medication_type_display', read_only=True)
    prescription_type_display = serializers.CharField(source='get_prescription_type_display', read_only=True)
    stock_status = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Medication
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class MedicationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate(self, data):
        # Validar que la fecha de vencimiento sea futura
        expiration_date = data.get('expiration_date')
        if expiration_date:
            from datetime import date
            if expiration_date <= date.today():
                raise serializers.ValidationError({
                    'expiration_date': 'La fecha de vencimiento debe ser futura'
                })
        
        # Validar que el stock mínimo no sea mayor al stock actual
        current_stock = data.get('current_stock', 0)
        minimum_stock = data.get('minimum_stock', 0)
        
        if minimum_stock > current_stock:
            raise serializers.ValidationError({
                'minimum_stock': 'El stock mínimo no puede ser mayor al stock actual'
            })
        
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class StockMovementSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    created_by_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = StockMovement
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by', 'stock_after')

    def validate(self, data):
        medication = data.get('medication')
        movement_type = data.get('movement_type')
        quantity = data.get('quantity')
        
        # Validar que las salidas no excedan el stock disponible
        if movement_type in ['VENTA', 'AJUSTE'] and quantity < 0:
            if medication and abs(quantity) > medication.current_stock:
                raise serializers.ValidationError({
                    'quantity': f'No se puede reducir más stock del disponible ({medication.current_stock})'
                })
        
        return data

    def create(self, validated_data):
        medication = validated_data['medication']
        quantity = validated_data['quantity']
        
        # Calcular nuevo stock
        new_stock = medication.current_stock + quantity
        validated_data['stock_after'] = new_stock
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        
        # Crear el movimiento
        movement = super().create(validated_data)
        
        # Actualizar el stock del medicamento
        medication.current_stock = new_stock
        medication.save()
        
        return movement 