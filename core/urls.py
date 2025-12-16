from django.urls import path
from .views import simulador, listado_operaciones

urlpatterns = [
    path("simulador/", simulador, name="simulador"),
    path("operaciones/", listado_operaciones, name="operaciones"),
]
