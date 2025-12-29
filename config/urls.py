from django.urls import path
from . import views

urlpatterns = [
    path('proyectos/', views.lista_proyectos, name='proyectos'),
    path('proyectos/<int:proyecto_id>/', views.proyecto_detalle, name='proyecto_detalle'),
    path('proyectos/<int:proyecto_id>/gastos/', views.proyecto_gastos, name='proyecto_gastos'),
    path('simulaciones/<int:simulacion_id>/convertir/', views.convertir_simulacion_a_proyecto, name='convertir_simulacion'),
]
