from rest_framework import serializers
from .models import ReportTemplate, ReportExecution, ReportFilter, ReportSchedule

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class ReportExecutionSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_ready = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = ReportExecution
        fields = '__all__'
        read_only_fields = (
            'id', 'status', 'file_path', 'file_size', 'total_rows', 
            'execution_time', 'error_message', 'requested_by', 
            'requested_at', 'started_at', 'completed_at', 'expires_at',
            'download_count'
        )

    def create(self, validated_data):
        validated_data['requested_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class ReportFilterSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = ReportFilter
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data)

class ReportScheduleSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = '__all__'
        read_only_fields = ('created_at', 'created_by', 'last_execution')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.get('id', 0)
        return super().create(validated_data) 