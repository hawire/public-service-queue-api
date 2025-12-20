"""
Citizen API views with error handling.
"""
import logging
from django.shortcuts import get_object_or_404
from django.db import DatabaseError
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Citizen
from .serializers import CitizenSerializer

logger = logging.getLogger(__name__)


class CitizenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing citizens with error handling.
    """
    queryset = Citizen.objects.all()
    serializer_class = CitizenSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'national_id', 'phone_number']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['created_at']

    def create(self, request, *args, **kwargs):
        """
        Create a citizen with duplicate national_id check.
        """
        try:
            national_id = request.data.get('national_id')
            
            # Check for duplicate national_id
            if national_id and Citizen.objects.filter(national_id=national_id).exists():
                return Response(
                    {
                        "error": "Duplicate national ID",
                        "message": f"A citizen with national ID {national_id} already exists"
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            return super().create(request, *args, **kwargs)
            
        except ValidationError as e:
            logger.warning(f"Citizen creation validation error: {e.detail}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error in citizen creation: {str(e)}")
            return Response(
                {"error": "Database error. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Unexpected error in citizen creation: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        Update citizen with error handling.
        """
        try:
            citizen = self.get_object()
            
            # If national_id is being changed, check for duplicates
            new_national_id = request.data.get('national_id')
            if new_national_id and new_national_id != citizen.national_id:
                if Citizen.objects.filter(national_id=new_national_id).exists():
                    return Response(
                        {
                            "error": "Duplicate national ID",
                            "message": f"Another citizen already has national ID {new_national_id}"
                        },
                        status=status.HTTP_409_CONFLICT
                    )
            
            return super().update(request, *args, **kwargs)
            
        except ValidationError as e:
            logger.warning(f"Citizen update validation error: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Error updating citizen: {str(e)}")
            return Response(
                {"error": "Failed to update citizen"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='tickets')
    def citizen_tickets(self, request, pk=None):
        """
        Get all tickets for a specific citizen.
        """
        try:
            citizen = self.get_object()
            tickets = citizen.ticket_set.all()  # Assuming reverse relation
            
            from tickets.serializers import TicketSerializer # type: ignore
            serializer = TicketSerializer(tickets, many=True)
            
            return Response({
                "citizen": CitizenSerializer(citizen).data,
                "tickets": serializer.data,
                "ticket_count": len(serializer.data)
            })
            
        except Exception as e:
            logger.error(f"Error getting citizen tickets: {str(e)}")
            return Response(
                {"error": "Failed to retrieve tickets"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete citizen with dependent tickets check.
        """
        try:
            citizen = self.get_object()
            
            # Check if citizen has tickets
            if hasattr(citizen, 'ticket_set') and citizen.ticket_set.exists():
                return Response(
                    {
                        "error": "Cannot delete citizen with active tickets",
                        "ticket_count": citizen.ticket_set.count(),
                        "suggestion": "Delete or reassign tickets first"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            citizen_data = CitizenSerializer(citizen).data
            response = super().destroy(request, *args, **kwargs)
            
            logger.info(f"Citizen deleted: {citizen_data['first_name']} {citizen_data['last_name']}")
            
            return Response(
                {
                    "message": "Citizen deleted successfully",
                    "citizen": citizen_data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error deleting citizen: {str(e)}")
            return Response(
                {"error": "Failed to delete citizen"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )