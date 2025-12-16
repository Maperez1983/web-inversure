from django.urls import path
from core import views

urlpatterns = [
    path("", views.simulador, name="home"),
    path("simulador/", views.simulador, name="simulador"),
    path("operaciones/", views.operaciones, name="operaciones"),
]
