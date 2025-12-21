from django.urls import path
from . import views

urlpatterns = [
    path("", views.simulador, name="simulador"),
    path("proyectos/", views.lista_proyectos, name="lista_proyectos"),
]
