from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta, time
from django.conf import settings
import requests
from .models import Appointment, VeterinarianSchedule, AppointmentBlock
from .serializers import (
    AppointmentSerializer, AppointmentCreateSerializer, AppointmentListSerializer,
    VeterinarianScheduleSerializer, AppointmentBlockSerializer, AgendaSerializer
)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'appointment_type', 'priority', 'veterinarian_id', 'patient_id', 'appointment_date']
    search_fields = ['reason', 'notes', 'contact_phone']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at', 'priority']
    ordering = ['appointment_date', 'appointment_time']

    def get_serializer_class(self):
        if self.action == 'list':
            return AppointmentListSerializer
        elif self.action == 'create':
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def perform_create(self, serializer):
        """Agregar el usuario que crea la cita"""
        serializer.save(created_by=self.request.user.get('id', 0))

    def get_queryset(self):
        """Personalizar queryset según parámetros"""
        queryset = super().get_queryset()
        
        # Filtrar por rango de fechas
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
            
        return queryset

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirmar una cita"""
        appointment = self.get_object()
        if appointment.status != 'AGENDADA':
            return Response(
                {'error': 'Solo se pueden confirmar citas agendadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'CONFIRMADA'
        appointment.confirmed_at = datetime.now()
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar una cita"""
        appointment = self.get_object()
        if appointment.status in ['COMPLETADA', 'CANCELADA']:
            return Response(
                {'error': 'No se puede cancelar una cita completada o ya cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'CANCELADA'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Iniciar una cita (marcar como en progreso)"""
        appointment = self.get_object()
        if appointment.status != 'CONFIRMADA':
            return Response(
                {'error': 'Solo se pueden iniciar citas confirmadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'EN_PROGRESO'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Completar una cita"""
        appointment = self.get_object()
        if appointment.status != 'EN_PROGRESO':
            return Response(
                {'error': 'Solo se pueden completar citas en progreso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'COMPLETADA'
        appointment.save()
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def agenda(self, request):
        """Obtener agenda de un veterinario para una fecha"""
        veterinarian_id = request.query_params.get('veterinarian_id')
        date_str = request.query_params.get('date')
        
        if not veterinarian_id or not date_str:
            return Response(
                {'error': 'Se requieren los parámetros veterinarian_id y date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener citas del día
        appointments = Appointment.objects.filter(
            veterinarian_id=veterinarian_id,
            appointment_date=date
        ).order_by('appointment_time')
        
        # Obtener horarios disponibles
        available_slots = self._get_available_slots(veterinarian_id, date)
        
        # Obtener bloqueos
        blocked_periods = self._get_blocked_periods(veterinarian_id, date)
        
        agenda_data = {
            'date': date,
            'veterinarian_id': veterinarian_id,
            'appointments': AppointmentListSerializer(appointments, many=True).data,
            'available_slots': available_slots,
            'blocked_periods': blocked_periods
        }
        
        return Response(agenda_data)

    def _get_available_slots(self, veterinarian_id, date):
        """Calcular horarios disponibles para un veterinario en una fecha"""
        # Obtener horario de trabajo
        day_name = date.strftime('%A').upper()
        day_mapping = {
            'MONDAY': 'LUNES', 'TUESDAY': 'MARTES', 'WEDNESDAY': 'MIERCOLES',
            'THURSDAY': 'JUEVES', 'FRIDAY': 'VIERNES', 'SATURDAY': 'SABADO', 'SUNDAY': 'DOMINGO'
        }
        
        try:
            schedule = VeterinarianSchedule.objects.get(
                veterinarian_id=veterinarian_id,
                day_of_week=day_mapping[day_name],
                is_active=True
            )
        except VeterinarianSchedule.DoesNotExist:
            return []
        
        # Generar slots cada 30 minutos
        slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)
        slot_duration = timedelta(minutes=settings.APPOINTMENT_DURATION_MINUTES)
        
        while current_time + slot_duration <= end_time:
            slot_time = current_time.time()
            
            # Verificar si el slot está ocupado
            if not self._is_slot_occupied(veterinarian_id, date, slot_time):
                slots.append(slot_time)
            
            current_time += slot_duration
        
        return slots

    def _is_slot_occupied(self, veterinarian_id, date, slot_time):
        """Verificar si un slot está ocupado"""
        # Verificar citas existentes
        existing_appointments = Appointment.objects.filter(
            veterinarian_id=veterinarian_id,
            appointment_date=date,
            status__in=['AGENDADA', 'CONFIRMADA', 'EN_PROGRESO']
        )
        
        slot_datetime = datetime.combine(date, slot_time)
        slot_end = slot_datetime + timedelta(minutes=settings.APPOINTMENT_DURATION_MINUTES)
        
        for apt in existing_appointments:
            apt_start = datetime.combine(apt.appointment_date, apt.appointment_time)
            apt_end = apt_start + timedelta(minutes=apt.duration_minutes)
            
            # Verificar solapamiento
            if not (slot_end <= apt_start or slot_datetime >= apt_end):
                return True
        
        # Verificar bloqueos
        blocks = AppointmentBlock.objects.filter(
            veterinarian_id=veterinarian_id,
            is_active=True,
            start_datetime__lt=slot_end,
            end_datetime__gt=slot_datetime
        )
        
        return blocks.exists()

    def _get_blocked_periods(self, veterinarian_id, date):
        """Obtener períodos bloqueados para un veterinario en una fecha"""
        start_datetime = datetime.combine(date, time.min)
        end_datetime = datetime.combine(date, time.max)
        
        blocks = AppointmentBlock.objects.filter(
            veterinarian_id=veterinarian_id,
            is_active=True,
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        )
        
        blocked_periods = []
        for block in blocks:
            blocked_periods.append({
                'start': block.start_datetime.time() if block.start_datetime.date() == date else time.min,
                'end': block.end_datetime.time() if block.end_datetime.date() == date else time.max,
                'reason': block.reason
            })
        
        return blocked_periods

    @action(detail=False, methods=['get'])
    def weekly_agenda(self, request):
        """Obtener agenda semanal de un veterinario"""
        veterinarian_id = request.query_params.get('veterinarian_id')
        week_start = request.query_params.get('week_start')
        
        if not veterinarian_id or not week_start:
            return Response(
                {'error': 'Se requieren los parámetros veterinarian_id y week_start'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        end_date = start_date + timedelta(days=6)
        
        appointments = Appointment.objects.filter(
            veterinarian_id=veterinarian_id,
            appointment_date__range=[start_date, end_date]
        ).order_by('appointment_date', 'appointment_time')
        
        # Agrupar por fecha
        agenda_by_date = {}
        current_date = start_date
        while current_date <= end_date:
            date_appointments = appointments.filter(appointment_date=current_date)
            agenda_by_date[current_date.isoformat()] = {
                'date': current_date,
                'appointments': AppointmentListSerializer(date_appointments, many=True).data,
                'available_slots': self._get_available_slots(veterinarian_id, current_date),
                'blocked_periods': self._get_blocked_periods(veterinarian_id, current_date)
            }
            current_date += timedelta(days=1)
        
        return Response(agenda_by_date)

class VeterinarianScheduleViewSet(viewsets.ModelViewSet):
    queryset = VeterinarianSchedule.objects.all()
    serializer_class = VeterinarianScheduleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['veterinarian_id', 'day_of_week', 'is_active']

class AppointmentBlockViewSet(viewsets.ModelViewSet):
    queryset = AppointmentBlock.objects.all()
    serializer_class = AppointmentBlockSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['veterinarian_id', 'is_active']
    ordering = ['start_datetime']

    def perform_create(self, serializer):
        """Agregar el usuario que crea el bloqueo"""
        serializer.save(created_by=self.request.user.get('id', 0)) 