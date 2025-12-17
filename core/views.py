from django.shortcuts import render


def simulador(request):
    resultado = None

    if request.method == "POST":

        # ---------- DATOS PRINCIPALES ----------
        precio_compra = float(request.POST.get("precio_compra") or 0)
        precio_venta = float(request.POST.get("precio_venta") or 0)
        meses = float(request.POST.get("meses") or 0)
        financiacion = float(request.POST.get("financiacion") or 0)

        # ---------- GASTOS ADQUISICIÓN ----------
        gestoria_compra = float(request.POST.get("gestoria_compra") or 0)
        captacion = float(request.POST.get("captacion") or 0)
        otros_adquisicion = float(request.POST.get("otros_adquisicion") or 0)

        # Automáticos (Andalucía)
        itp = precio_compra * 0.02
        notaria = precio_compra * 0.002
        registro = precio_compra * 0.002

        gastos_adquisicion = (
            itp + notaria + registro +
            gestoria_compra + captacion + otros_adquisicion
        )

        # ---------- INVERSIÓN INICIAL ----------
        reforma = float(request.POST.get("reforma") or 0)
        limpieza_inicial = float(request.POST.get("limpieza_inicial") or 0)
        mobiliario = float(request.POST.get("mobiliario") or 0)
        otros_puesta_marcha = float(request.POST.get("otros_puesta_marcha") or 0)

        inversion_inicial = (
            reforma + limpieza_inicial +
            mobiliario + otros_puesta_marcha
        )

        # ---------- GASTOS RECURRENTES ----------
        comunidad = float(request.POST.get("comunidad") or 0)
        ibi = float(request.POST.get("ibi") or 0)
        seguros = float(request.POST.get("seguros") or 0)
        suministros = float(request.POST.get("suministros") or 0)
        limpieza_periodica = float(request.POST.get("limpieza_periodica") or 0)
        ocupas = float(request.POST.get("ocupas") or 0)
        otros_recurrentes = float(request.POST.get("otros_recurrentes") or 0)

        gastos_recurrentes = (
            comunidad + ibi + seguros + suministros +
            limpieza_periodica + ocupas + otros_recurrentes
        )

        # ---------- GASTOS DE VENTA ----------
        plusvalia = float(request.POST.get("plusvalia") or 0)
        inmobiliaria = float(request.POST.get("inmobiliaria") or 0)
        gestoria_venta = float(request.POST.get("gestoria_venta") or 0)
        otros_venta = float(request.POST.get("otros_venta") or 0)

        gastos_venta = (
            plusvalia + inmobiliaria +
            gestoria_venta + otros_venta
        )

        # ---------- INVERSIÓN TOTAL ----------
        inversion_total = (
            precio_compra +
            gastos_adquisicion +
            inversion_inicial +
            gastos_recurrentes +
            gastos_venta
        )

        # ---------- BENEFICIOS ----------
        beneficio_bruto = precio_venta - inversion_total

        beneficio_inversure = beneficio_bruto * 0.40
        beneficio_participes = beneficio_bruto * 0.60

        # ---------- RENTABILIDADES ----------
        rentabilidad_total = (
            (beneficio_bruto / inversion_total) * 100
            if inversion_total > 0 else 0
        )

        rentabilidad_anual = (
            rentabilidad_total * (12 / meses)
            if meses > 0 else 0
        )

        roi = rentabilidad_total

        # ---------- INDICADORES DE CONTROL ----------
        ratio_beneficio_coste = (
            beneficio_bruto / inversion_total
            if inversion_total > 0 else 0
        )

        breakeven = inversion_total
        colchon_seguridad = precio_venta - breakeven

        operacion_apta = roi >= 15

        # ---------- RESULTADO FINAL ----------
        resultado = {
            "inversion_total": round(inversion_total, 2),
            "beneficio_bruto": round(beneficio_bruto, 2),
            "beneficio_inversure": round(beneficio_inversure, 2),
            "beneficio_participes": round(beneficio_participes, 2),
            "rentabilidad": round(rentabilidad_total, 2),
            "rentabilidad_anual": round(rentabilidad_anual, 2),
            "roi": round(roi, 2),
            "ratio": round(ratio_beneficio_coste, 3),
            "breakeven": round(breakeven, 2),
            "colchon": round(colchon_seguridad, 2),
            "apta": operacion_apta,
        }

    return render(request, "core/simulador.html", {
        "resultado": resultado
    })
