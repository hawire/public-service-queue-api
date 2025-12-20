from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from .models import Citizen
from .serializers import CitizenSerializer

class CitizenViewSet(ModelViewSet):
    queryset = Citizen.objects.all()
    serializer_class = CitizenSerializer
