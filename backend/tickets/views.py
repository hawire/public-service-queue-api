"""
Ticket API views with comprehensive error handling.
"""
import logging
from django.shortcuts import get_object_or_404
from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from .models import Ticket
from .serializers import TicketSerializer
from services.models import Service # type: ignore

logger = logging.getLogger(__name__)


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tickets with auto-numbering and queue management.
    """
    queryset = Ticket.objects.all().select_related('service', 'citizen')
    serializer_class = TicketSerializer
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['status', 'created_at', 'number', 'service__name']
    ordering = ['created_at']
    search_fields = ['citizen__first_name', 'citizen__last_name', 'number']

    def get_permissions(self):
        """
        Custom permissions: Staff required for modifications, anyone can view.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'serve_next', 'next_ticket']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def create(self, request, *args, **kwargs):
        """
        Create a new ticket with automatic numbering.
        """
        try:
            with transaction.atomic():
                # Validate service exists
                service_id = request.data.get('service')
                if not service_id:
                    raise ValidationError({"service": "Service ID is required"})
                
                try:
                    service = Service.objects.get(id=service_id)
                except Service.DoesNotExist:
                    return Response(
                        {"error": "Service not found", "service_id": service_id},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Generate ticket number
                last_ticket = Ticket.objects.filter(
                    service=service
                ).order_by('-created_at').first()
                
                if last_ticket and last_ticket.number:
                    try:
                        last_number = int(last_ticket.number.split('-')[-1])
                        new_number = f"{service.code}-{last_number + 1:04d}"
                    except (ValueError, IndexError):
                        new_number = f"{service.code}-0001"
                else:
                    new_number = f"{service.code}-0001"
                
                # Add auto-generated number to request data
                request.data._mutable = True
                request.data['number'] = new_number
                request.data._mutable = False
                
                # Proceed with default creation
                return super().create(request, *args, **kwargs)
                
        except ValidationError as e:
            logger.warning(f"Ticket creation validation error: {e.detail}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error during ticket creation: {str(e)}")
            return Response(
                {"error": "Database error. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in ticket creation: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='next')
    def next_ticket(self, request):
        """
        Returns the next pending ticket for a service with error handling.
        """
        try:
            service_id = request.query_params.get('service')
            
            if not service_id:
                return Response(
                    {"error": "Service ID is required as query parameter"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate service exists
            try:
                service = Service.objects.get(id=service_id)
            except Service.DoesNotExist:
                return Response(
                    {"error": f"Service with ID {service_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get next pending ticket
            ticket = Ticket.objects.filter(
                service_id=service_id, status='pending'
            ).select_related('citizen', 'service').order_by('created_at').first()
            
            if not ticket:
                return Response(
                    {"message": f"No pending tickets for service: {service.name}"},
                    status=status.HTTP_204_NO_CONTENT
                )
            
            serializer = TicketSerializer(ticket)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except DatabaseError as e:
            logger.error(f"Database error in next_ticket: {str(e)}")
            return Response(
                {"error": "Unable to retrieve tickets. Database error."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in next_ticket: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='serve-next')
    def serve_next(self, request):
        """
        Mark the next pending ticket as 'serving' with atomic transaction.
        """
        try:
            with transaction.atomic():
                service_id = request.data.get('service')
                
                if not service_id:
                    return Response(
                        {"error": "Service ID is required in request body"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Validate service exists
                try:
                    service = Service.objects.get(id=service_id)
                except Service.DoesNotExist:
                    return Response(
                        {"error": f"Service with ID {service_id} not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Find and update the next pending ticket
                ticket = Ticket.objects.filter(
                    service_id=service_id, status='pending'
                ).select_related('citizen', 'service').order_by('created_at').first()
                
                if not ticket:
                    return Response(
                        {"message": f"No pending tickets for service: {service.name}"},
                        status=status.HTTP_204_NO_CONTENT
                    )
                
                # Update status
                old_status = ticket.status
                ticket.status = 'serving'
                
                # Validate the status change
                try:
                    ticket.full_clean()
                    ticket.save(update_fields=['status', 'updated_at'])
                except DjangoValidationError as e:
                    logger.error(f"Ticket validation failed: {e.message_dict}")
                    return Response(
                        {"error": "Invalid status transition", "details": e.message_dict},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Log the status change
                logger.info(
                    f"Ticket {ticket.number} status changed: {old_status} -> {ticket.status} "
                    f"(Service: {service.name}, Citizen: {ticket.citizen})"
                )
                
                serializer = TicketSerializer(ticket)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except DatabaseError as e:
            logger.error(f"Database error in serve_next: {str(e)}")
            return Response(
                {"error": "Database transaction failed. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in serve_next: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        Custom delete with logging and error handling.
        """
        try:
            ticket = self.get_object()
            ticket_data = {
                "number": ticket.number,
                "service": str(ticket.service),
                "citizen": str(ticket.citizen)
            }
            
            response = super().destroy(request, *args, **kwargs)
            
            # Log successful deletion
            logger.info(f"Ticket deleted: {ticket_data}")
            
            return Response(
                {"message": "Ticket deleted successfully", "ticket": ticket_data},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error deleting ticket: {str(e)}")
            return Response(
                {"error": "Failed to delete ticket"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )