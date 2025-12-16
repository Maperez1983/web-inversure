from django.shortcuts import render
from .models import Operacion


def to_float(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def simulador(request):
    result = None

    if request.method == "POST":

        # =====================
        # DATOS PRINCIPALES
        # =====================
        precio_compra = to_float(request.POST.get("precio_compra"))
        precio_venta = to_float(request.POST.get("precio_venta"))
        meses = to_float(request.POST.get("meses"))

        # =====================
        # GASTOS AUTOMÁTICOS
        # =====================
        itp = precio_compra * 0.02
        notaria = precio_compra * 0.002
        registro = precio_compra * 0.002

        # =====================
        # ADQUISICIÓN
        # =====================
        gestoria_compra = to_float(request.POST.get("gestoria_compra"))
        comisiones_captacion = to_float(request.POST.get("comisiones_captacion"))
        otros_adquisicion = to_float(request.POST.get("otros_adquisicion"))

        # =====================
        # INVERSIÓN INICIAL
        # =====================
        reforma = to_float(request.POST.get("reforma"))
        limpieza_inicial = to_float(request.POST.get("limpieza_inicial"))
        mobiliario = to_float(request.POST.get("mobiliario"))
        otros_puesta_marcha = to_float(request.POST.get("otros_puesta_marcha"))

        # =====================
        # RECURRENTES
        # =====================
        comunidad = to_float(request.POST.get("comunidad"))
        ibi = to_float(request.POST.get("ibi"))
        seguros = to_float(request.POST.get("seguros"))
        suministros = to_float(request.POST.get("suministros"))
        limpieza = to_float(request.POST.get("limpieza"))
        ocupas = to_float(request.POST.get("ocupas"))
        otros_recurrentes = to_float(request.POST.get("otros_recurrentes"))

        gastos_recurrentes = (
            comunidad + ibi + seguros + suministros +
            limpieza + ocupas + otros_recurrentes
        )

        # =====================
        # VENTA
        # =====================
        plusvalia = to_float(request.POST.get("plusvalia"))
        inmobiliaria = to_float(request.POST.get("inmobiliaria"))
        gestoria_venta = to_float(request.POST.get("gestoria_venta"))
        otros_venta = to_float(request.POST.get("otros_venta"))

        # =====================
        # CÁLCULOS
        # =====================
        inversion_total = (
            precio_compra + itp + notaria + registro +
            gestoria_compra + comisiones_captacion + otros_adquisicion +
            reforma + limpieza_inicial + mobiliario + otros_puesta_marcha +
            gastos_recurrentes +
            plusvalia + inmobiliaria + gestoria_venta + otros_venta
        )

        beneficio_bruto = precio_venta - inversion_total

        beneficio_inversure = beneficio_bruto * 0.40
        gastos_administracion = beneficio_inversure * 0.05
        gastos_comerciales = beneficio_inversure * 0.05
        beneficio_neto_inversure = beneficio_inversure - gastos_administracion - gastos_comerciales

        beneficio_participes = beneficio_bruto * 0.60

        rentabilidad_total = (beneficio_bruto / inversion_total * 100) if inversion_total else 0
        rentabilidad_anualizada = (rentabilidad_total / meses * 12) if meses else 0

        roi_objetivo = 15
        cumple_roi = rentabilidad_total >= roi_objetivo

        ratio_beneficio_coste = beneficio_bruto / inversion_total if inversion_total else 0
        precio_breakeven = inversion_total
        colchon_seguridad = precio_venta - precio_breakeven

        result = {
            "inversion_total": round(inversion_total, 2),
            "beneficio_bruto": round(beneficio_bruto, 2),
            "beneficio_inversure": round(beneficio_inversure, 2),
            "gastos_administracion": round(gastos_administracion, 2),
            "gastos_comerciales": round(gastos_comerciales, 2),
            "beneficio_neto_inversure": round(beneficio_neto_inversure, 2),
            "beneficio_participes": round(beneficio_participes, 2),
            "rentabilidad_total": round(rentabilidad_total, 2),
            "rentabilidad_anualizada": round(rentabilidad_anualizada, 2),
            "roi_objetivo": roi_objetivo,
            "cumple_roi": cumple_roi,
            "ratio_beneficio_coste": round(ratio_beneficio_coste, 3),
            "precio_breakeven": round(precio_breakeven, 2),
            "colchon_seguridad": round(colchon_seguridad, 2),
        }

        Operacion.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            precio_compra=precio_compra,
            precio_venta=precio_venta,
            meses=meses,
            inversion_total=inversion_total,
            beneficio_bruto=beneficio_bruto,
            beneficio_inversure=beneficio_inversure,
            beneficio_neto_inversure=beneficio_neto_inversure,
            beneficio_participes=beneficio_participes,
            rentabilidad_total=rentabilidad_total,
            rentabilidad_anualizada=rentabilidad_anualizada,
            cumple_roi=cumple_roi,
            precio_breakeven=precio_breakeven,
            colchon_seguridad=colchon_seguridad,
        )

    return render(request, "core/simulador.html", {"result": result})


def listado_operaciones(request):
    operaciones = Operacion.objects.order_by("-fecha")
    return render(request, "core/operaciones.html", {"operaciones": operaciones})
