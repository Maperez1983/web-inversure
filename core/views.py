from django.shortcuts import render
from .models import Operacion

# =====================
# SIMULADOR
# =====================
def simulador(request):
    """
    Muestra el formulario del simulador de operaciones.
    En este paso NO hay cálculos.
    """
    return render(request, "core/simulador.html")


# =====================
# OPERACIONES
# =====================
def operaciones(request):
    """
    Lista de operaciones guardadas.
    """
    operaciones = Operacion.objects.all().order_by("-fecha")
    return render(request, "core/operaciones.html", {
        "operaciones": operaciones
    })
