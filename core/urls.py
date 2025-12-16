from django.urls import path
from . import views

urlpatterns = [
    path("", views.simulador, name="home"),
    path("simulador/", views.simulador, name="simulador"),
    path("operaciones/", views.operaciones, name="operaciones"),
]
