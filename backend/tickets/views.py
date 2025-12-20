from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Ticket
from .serializers import TicketSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['status', 'created_at', 'number']
    ordering = ['created_at']

    # Only staff users can create, update, delete tickets
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'serve_next']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    @action(detail=False, methods=['get'], url_path='next')
    def next_ticket(self, request):
        """Returns the next pending ticket for a service."""
        service_id = request.query_params.get('service')
        if not service_id:
            return Response({"error": "Service ID is required"}, status=400)
        
        ticket = Ticket.objects.filter(
            service_id=service_id, status='pending'
        ).order_by('created_at').first()
        
        if ticket:
            return Response(TicketSerializer(ticket).data)
        return Response({"message": "No pending tickets"})

    @action(detail=False, methods=['post'], url_path='serve-next')
    def serve_next(self, request):
        """Mark the next pending ticket as 'serving'."""
        service_id = request.data.get('service')
        if not service_id:
            return Response({"error": "Service ID is required"}, status=400)

        ticket = Ticket.objects.filter(
            service_id=service_id, status='pending'
        ).order_by('created_at').first()

        if ticket:
            ticket.status = 'serving'
            ticket.save()
            return Response(TicketSerializer(ticket).data)
        return Response({"message": "No pending tickets"})
