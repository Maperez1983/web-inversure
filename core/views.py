
from django.shortcuts import render, redirect
from decimal import Decimal
from .models import Proyecto, Cliente, Participacion, Simulacion

try:
    import pandas as pd
except ImportError:
    pd = None
from django.contrib import messages
import requests
import xml.etree.ElementTree as ET
from django.http import JsonResponse


# Nueva vista home
def home(request):
    return render(request, "core/home.html")


def parse_euro(value):
    if value in (None, ""):
        return 0.0
    try:
        return float(
            str(value)
            .replace(".", "")
            .replace(",", ".")
            .replace("€", "")
            .replace("\xa0", "")
            .strip()
        )
    except Exception:
        return 0.0


def consultar_catastro_por_rc(ref_catastral):
    if not ref_catastral:
        return None

    # URL oficial de consulta por referencia catastral (no scraping)
    url = "https://www.sedecatastro.gob.es/Accesos/SECAccesos.aspx"

    return {
        "direccion": None,
        "municipio": None,
        "provincia": None,
        "lat": None,
        "lon": None,
        "url": url,
        "ref": ref_catastral,
    }

def simulador(request):
    editable = True  # BLINDAJE: siempre inicializado para evitar UnboundLocalError
    proyectos = Proyecto.objects.all().order_by("-creado", "-id")
    resultado = None
    proyecto = None

    # === CARGA DE PROYECTO POR NOMBRE (GET) ===
    nombre_get = request.GET.get("proyecto")
    if nombre_get:
        proyecto = Proyecto.objects.filter(nombre=nombre_get).first()

    # === REGLAS POR ESTADO (FASE A) ===
    # editable se calculará tras POST

    if request.method == "POST":
        data = request.POST
        accion = data.get("accion")
        estado_post = data.get("estado") or (proyecto.estado if proyecto else "ESTUDIO")
        estado_post = estado_post.lower()
        # --- Cálculo puro sin guardar ---
        solo_calculo = data.get("solo_calculo") == "1"
        # === BLINDAJE GLOBAL OBLIGATORIO ===
        plusvalia = 0.0
        inmobiliaria = 0.0
        gestion_comercial = 0.0
        gestion_administracion = 0.0
        gastos_venta = 0.0

        nombre_proyecto = data.get("nombre")
        proyecto = None

        # PASO 1: Detección simplificada de cambio de estado
        if accion == "cambiar_estado":
            if nombre_proyecto:
                proyecto = Proyecto.objects.filter(nombre=nombre_proyecto).first()
                if proyecto:
                    proyecto.estado = estado_post
                    proyecto.save(update_fields=["estado"])
            editable = True
            if proyecto and proyecto.estado and proyecto.estado.lower() in ["cerrado", "cerrado_positivo"]:
                editable = False
            return render(
                request,
                "core/simulador.html",
                {
                    "proyectos": proyectos,
                    "resultado": resultado,
                    "proyecto": proyecto,
                    "editable": editable,
                },
            )

        if nombre_proyecto:
            proyecto = Proyecto.objects.filter(nombre=nombre_proyecto).first()
            # BLOQUEO POR ESTADO: si el proyecto está cerrado positivamente, no se permite recalcular ni sobrescribir
            if proyecto and proyecto.estado and proyecto.estado.lower() == "cerrado_positivo":
                resultado = {
                    "valor_adquisicion": round(proyecto.precio_compra_inmueble or 0, 2),
                    "precio_venta": round(proyecto.precio_venta_estimado or 0, 2),
                    "beneficio_neto": round(proyecto.beneficio_neto or 0, 2),
                    "roi": round(proyecto.roi or 0, 2),
                    "viable": (proyecto.roi or 0) >= 15,
                    "margen_neto": 0,
                    "colchon_seguridad": 0,
                    "ratio_euro": 0,
                    "precio_minimo_venta": 0,
                }
                editable = True
                if proyecto and proyecto.estado and proyecto.estado.lower() in ["cerrado", "cerrado_positivo"]:
                    editable = False
                return render(
                    request,
                    "core/simulador.html",
                    {
                        "proyectos": proyectos,
                        "resultado": resultado,
                        "proyecto": proyecto,
                        "editable": editable,
                    },
                )

        """
        ============================================================
        MOTOR DE CÁLCULO – SIMULADOR INVERSURE (CIERRE DEFINITIVO)
        ============================================================

        Este bloque define las reglas económicas base del simulador.
        Estas reglas se consideran ESTABLES y NO deben modificarse
        sin decisión estratégica expresa.

        --- DEFINICIONES CLAVE ---

        1) Precio de escritura
           Valor introducido por el usuario en escritura pública.

        2) Gastos automáticos de adquisición (sobre precio escritura):
           - Notaría: 0,20 % (mínimo 500 €)
           - Registro: 0,20 % (mínimo 500 €)
           - ITP: 2 %

        3) Valor de adquisición:
           Precio de escritura
           + gastos de adquisición
           + inversión inicial
           + gastos recurrentes

           (Los gastos de venta NO forman parte del valor de adquisición)

        4) Precio de venta:
           Por defecto: media de valoraciones.
           Puede ser sobrescrito manualmente para simulación de escenarios.

        5) Beneficio base:
           (Precio de venta – gastos de venta) – valor de adquisición

        6) Gastos de gestión:
           - Gestión comercial: 5 % del beneficio base
           - Gestión administrativa: 5 % del beneficio base

           (Solo se aplican sobre beneficio, nunca sobre costes)

        7) Beneficio neto:
           Beneficio base – gastos de gestión

        8) ROI (Return on Investment):
           ROI = beneficio neto / valor de adquisición

        9) Viabilidad:
           Una operación se considera VIABLE si:
           ROI >= 15 %

        --- NOTAS IMPORTANTES ---

        - El botón "Calcular" siempre aplica estas reglas.
        - El formulario no redefine la lógica, solo aporta datos.
        - UX, escenarios y visualizaciones NO alteran este motor.
        - Este motor es la base para futuras operaciones reales.

        ============================================================
        """

        # === DATOS BASE ===
        # SIEMPRE leer todos los datos relevantes directamente del formulario (POST)
        precio_escritura = parse_euro(data.get("precio_propiedad"))
        precio_venta = parse_euro(data.get("precio_venta_estimado"))

        # === VALORACIONES ===
        val_idealista = parse_euro(data.get("val_idealista"))
        val_fotocasa = parse_euro(data.get("val_fotocasa"))
        val_registradores = parse_euro(data.get("val_registradores"))
        val_casafari = parse_euro(data.get("val_casafari"))
        val_tasacion = parse_euro(data.get("val_tasacion"))

        valores = [
            v for v in [
                val_idealista,
                val_fotocasa,
                val_registradores,
                val_casafari,
                val_tasacion,
            ] if v > 0
        ]
        media_valoraciones = sum(valores) / len(valores) if valores else 0

        # REGLA DEFINITIVA INVERSURE:
        # El precio estimado de venta SIEMPRE sale de la media de valoraciones
        # (el usuario no define manualmente el precio de venta)
        if media_valoraciones > 0:
            precio_venta = media_valoraciones

        # NOTARÍA (0,20 % con mínimo 500 €, editable, blindaje manual/proyecto)
        notaria_post = parse_euro(data.get("notaria"))
        if "notaria" in data and notaria_post >= 0:
            notaria = notaria_post
        elif proyecto and proyecto.notaria is not None:
            notaria = float(proyecto.notaria)
        else:
            notaria = max(float(precio_escritura) * 0.002, 500)

        # REGISTRO (0,20 % con mínimo 500 €, editable, blindaje manual/proyecto)
        registro_post = parse_euro(data.get("registro"))
        if "registro" in data and registro_post >= 0:
            registro = registro_post
        elif proyecto and proyecto.registro is not None:
            registro = float(proyecto.registro)
        else:
            registro = max(float(precio_escritura) * 0.002, 500)

        # ITP (2 % editable, blindaje manual/proyecto)
        itp_post = parse_euro(data.get("itp"))
        if "itp" in data and itp_post >= 0:
            itp = itp_post
        elif proyecto and proyecto.itp is not None:
            itp = float(proyecto.itp)
        else:
            itp = float(precio_escritura) * 0.02

        # === GASTOS MANUALES ===
        otros_gastos_compra = parse_euro(data.get("otros_gastos_compra"))

        # Inversión inicial y gastos recurrentes
        reforma = parse_euro(data.get("reforma"))
        limpieza_inicial = parse_euro(data.get("limpieza_inicial"))
        mobiliario = parse_euro(data.get("mobiliario"))
        otros_puesta_marcha = parse_euro(data.get("otros_puesta_marcha"))

        comunidad = parse_euro(data.get("comunidad"))
        ibi = parse_euro(data.get("ibi"))
        seguros = parse_euro(data.get("seguros"))
        suministros = parse_euro(data.get("suministros"))
        limpieza_periodica = parse_euro(data.get("limpieza_periodica"))
        ocupas = parse_euro(data.get("ocupas"))

        # === OBRA (DETALLE POR PARTIDAS) ===
        obra_demoliciones = parse_euro(data.get("obra_demoliciones"))
        obra_albanileria = parse_euro(data.get("obra_albanileria"))
        obra_fontaneria = parse_euro(data.get("obra_fontaneria"))
        obra_electricidad = parse_euro(data.get("obra_electricidad"))
        obra_carpinteria_interior = parse_euro(data.get("obra_carpinteria_interior"))
        obra_carpinteria_exterior = parse_euro(data.get("obra_carpinteria_exterior"))
        obra_cocina = parse_euro(data.get("obra_cocina"))
        obra_banos = parse_euro(data.get("obra_banos"))
        obra_pintura = parse_euro(data.get("obra_pintura"))
        obra_otros = parse_euro(data.get("obra_otros"))

        # === SEGURIDAD ===
        cerrajero = parse_euro(data.get("cerrajero"))
        alarma = parse_euro(data.get("alarma"))

        inversion_inicial = (
            float(reforma or 0)
            + float(limpieza_inicial or 0)
            + float(mobiliario or 0)
            + float(otros_puesta_marcha or 0)
        )

        gastos_recurrentes = (
            float(comunidad or 0)
            + float(ibi or 0)
            + float(seguros or 0)
            + float(suministros or 0)
            + float(limpieza_periodica or 0)
            + float(ocupas or 0)
        )

        # === VALOR DE ADQUISICIÓN (MODELO DEFINITIVO INVERSURE) ===
        # (Precio adquisición + Gastos adquisición) + Inversión inicial + Obra + Seguridad + Gastos recurrentes

        gastos_adquisicion = (
            float(notaria or 0)
            + float(registro or 0)
            + float(itp or 0)
            + float(otros_gastos_compra or 0)
        )

        gastos_obra = (
            float(obra_demoliciones or 0)
            + float(obra_albanileria or 0)
            + float(obra_fontaneria or 0)
            + float(obra_electricidad or 0)
            + float(obra_carpinteria_interior or 0)
            + float(obra_carpinteria_exterior or 0)
            + float(obra_cocina or 0)
            + float(obra_banos or 0)
            + float(obra_pintura or 0)
            + float(obra_otros or 0)
        )

        gastos_seguridad = (
            float(cerrajero or 0)
            + float(alarma or 0)
        )

        valor_adquisicion = (
            float(precio_escritura or 0)
            + gastos_adquisicion
            + float(inversion_inicial or 0)
            + gastos_obra
            + gastos_seguridad
            + float(gastos_recurrentes or 0)
        )

        # === GASTOS DE VENTA ===
        if estado_post != "estudio":
            plusvalia = float(parse_euro(data.get("plusvalia")) or 0)
            inmobiliaria = float(parse_euro(data.get("inmobiliaria")) or 0)
            gastos_venta = plusvalia + inmobiliaria

        # === VALOR DE TRANSMISIÓN ===
        valor_transmision = float(precio_venta or 0) - float(gastos_venta or 0)

        # === BENEFICIO REAL ===
        beneficio_base = valor_transmision - valor_adquisicion

        # === GESTIÓN COMERCIAL Y ADMINISTRACIÓN ===
        gestion_comercial = parse_euro(data.get("gestion_comercial"))
        if "gestion_comercial" not in data and beneficio_base > 0 and (not proyecto or proyecto.gestion_comercial in (None, 0)):
            gestion_comercial = beneficio_base * 0.05

        gestion_administracion = parse_euro(data.get("gestion_administracion"))
        if "gestion_administracion" not in data and beneficio_base > 0 and (not proyecto or proyecto.gestion_administracion in (None, 0)):
            gestion_administracion = beneficio_base * 0.05

        # === BENEFICIO NETO ===
        gestion_comercial = float(gestion_comercial or 0)
        gestion_administracion = float(gestion_administracion or 0)

        beneficio_neto = float(beneficio_base) - gestion_comercial - gestion_administracion

        # === ROI ===
        roi = (beneficio_neto / valor_adquisicion) * 100 if valor_adquisicion > 0 else 0

        # === VIABILIDAD ===
        viable = roi >= 15

        # === MÉTRICAS PRO (ANÁLISIS INVERSOR) ===

        # Margen neto sobre precio de venta (%)
        margen_neto = (beneficio_neto / precio_venta) * 100 if precio_venta > 0 else 0

        # Colchón de seguridad (%)
        # Cuánto puede bajar el precio de venta antes de perder beneficio
        colchon_seguridad = margen_neto

        # Ratio € ganado por € invertido
        # Ej: 0,15 € por cada € invertido
        ratio_euro = (beneficio_neto / valor_adquisicion) if valor_adquisicion > 0 else 0

        # Precio mínimo de venta para cumplir ROI mínimo del 15 %
        # Beneficio mínimo exigido = 15 % del valor de adquisición
        beneficio_minimo = valor_adquisicion * 0.15

        # Precio mínimo de venta = adquisición + gastos de venta + beneficio mínimo
        precio_minimo_venta = valor_adquisicion + gastos_venta + beneficio_minimo

        resultado = {
            "valor_adquisicion": round(valor_adquisicion, 2),
            "precio_venta": round(precio_venta, 2),
            "beneficio_neto": round(beneficio_neto, 2),
            "roi": round(roi, 2),
            "viable": viable,

            # Métricas inversor
            "margen_neto": round(margen_neto, 2),
            "colchon_seguridad": round(colchon_seguridad, 2),
            "ratio_euro": round(ratio_euro, 3),
            "precio_minimo_venta": round(precio_minimo_venta, 2),
        }

        # === CONSOLIDACIÓN MÉTRICAS INVERSOR (OPCIÓN 3) ===
        resultado["metricas_inversor"] = {
            "ratio_euro": round(ratio_euro, 3),
            "precio_minimo_venta": round(precio_minimo_venta, 2),
            "decision": "VIABLE" if viable else "NO VIABLE",
        }

        # === GUARDAR / ACTUALIZAR PROYECTO (CLAVE = NOMBRE) ===
        if nombre_proyecto:
            estado_post = data.get("estado", "ESTUDIO")
            meses_val = int(data.get("meses")) if data.get("meses") else None
            if proyecto:
                # === ACTUALIZAR PROYECTO EXISTENTE (SIN PÉRDIDA DE DATOS) ===
                # 2) Persistencia pasiva real: solo asignar si campo en POST (aunque vacío)
                if "meses" in data:
                    proyecto.meses = meses_val
                if "otros_gastos_compra" in data:
                    proyecto.otros_gastos_compra = otros_gastos_compra
                if "reforma" in data:
                    proyecto.reforma = reforma
                if "limpieza_inicial" in data:
                    proyecto.limpieza_inicial = limpieza_inicial
                if "mobiliario" in data:
                    proyecto.mobiliario = mobiliario
                if "otros_puesta_marcha" in data:
                    proyecto.otros_puesta_marcha = otros_puesta_marcha
                if "comunidad" in data:
                    proyecto.comunidad = comunidad
                if "ibi" in data:
                    proyecto.ibi = ibi
                if "seguros" in data:
                    proyecto.seguros = seguros
                if "suministros" in data:
                    proyecto.suministros = suministros
                if "limpieza_periodica" in data:
                    proyecto.limpieza_periodica = limpieza_periodica
                if "ocupas" in data:
                    proyecto.ocupas = ocupas
                # 1) Blindaje por fase (estudio vs operación)
                if estado_post.lower() != "estudio":
                    if "plusvalia" in data:
                        proyecto.plusvalia = plusvalia
                    if "inmobiliaria" in data:
                        proyecto.inmobiliaria = inmobiliaria
                    # Obra
                    if "obra_demoliciones" in data:
                        proyecto.obra_demoliciones = obra_demoliciones
                    if "obra_albanileria" in data:
                        proyecto.obra_albanileria = obra_albanileria
                    if "obra_fontaneria" in data:
                        proyecto.obra_fontaneria = obra_fontaneria
                    if "obra_electricidad" in data:
                        proyecto.obra_electricidad = obra_electricidad
                    if "obra_carpinteria_interior" in data:
                        proyecto.obra_carpinteria_interior = obra_carpinteria_interior
                    if "obra_carpinteria_exterior" in data:
                        proyecto.obra_carpinteria_exterior = obra_carpinteria_exterior
                    if "obra_cocina" in data:
                        proyecto.obra_cocina = obra_cocina
                    if "obra_banos" in data:
                        proyecto.obra_banos = obra_banos
                    if "obra_pintura" in data:
                        proyecto.obra_pintura = obra_pintura
                    if "obra_otros" in data:
                        proyecto.obra_otros = obra_otros
                    # Seguridad
                    if "cerrajero" in data:
                        proyecto.cerrajero = cerrajero
                    if "alarma" in data:
                        proyecto.alarma = alarma
                # NO modificar estos campos en estudio (ni poner a 0)
                if "val_idealista" in data:
                    proyecto.val_idealista = val_idealista
                if "val_fotocasa" in data:
                    proyecto.val_fotocasa = val_fotocasa
                if "val_registradores" in data:
                    proyecto.val_registradores = val_registradores
                if "val_casafari" in data:
                    proyecto.val_casafari = val_casafari
                if "val_tasacion" in data:
                    proyecto.val_tasacion = val_tasacion

                proyecto.precio_propiedad = precio_escritura
                proyecto.precio_compra_inmueble = valor_adquisicion
                proyecto.precio_venta_estimado = precio_venta
                # Blindaje de guardado solo si el campo viene en POST
                if "notaria" in data:
                    proyecto.notaria = notaria
                if "registro" in data:
                    proyecto.registro = registro
                if "itp" in data:
                    proyecto.itp = itp

                proyecto.media_valoraciones = media_valoraciones
                proyecto.gestion_comercial = gestion_comercial
                proyecto.gestion_administracion = gestion_administracion
                proyecto.beneficio_neto = beneficio_neto
                proyecto.roi = roi
                proyecto.estado = estado_post

                if not solo_calculo:
                    proyecto.save()
            else:
                # Crear nuevo proyecto (no blindamos en alta)
                proyecto = Proyecto.objects.create(
                    nombre=nombre_proyecto,
                    precio_propiedad=precio_escritura,
                    precio_compra_inmueble=valor_adquisicion,
                    precio_venta_estimado=precio_venta,
                    notaria=notaria,
                    registro=registro,
                    itp=itp,
                    beneficio_neto=beneficio_neto,
                    roi=roi,
                    val_idealista=val_idealista,
                    val_fotocasa=val_fotocasa,
                    val_registradores=val_registradores,
                    val_casafari=val_casafari,
                    val_tasacion=val_tasacion,
                    otros_gastos_compra=otros_gastos_compra,
                    reforma=reforma,
                    limpieza_inicial=limpieza_inicial,
                    mobiliario=mobiliario,
                    otros_puesta_marcha=otros_puesta_marcha,
                    comunidad=comunidad,
                    ibi=ibi,
                    seguros=seguros,
                    suministros=suministros,
                    limpieza_periodica=limpieza_periodica,
                    ocupas=ocupas,
                    plusvalia=plusvalia,
                    inmobiliaria=inmobiliaria,
                    estado=estado_post,
                    media_valoraciones=media_valoraciones,
                    gestion_comercial=gestion_comercial,
                    gestion_administracion=gestion_administracion,
                    meses=meses_val,
                    obra_demoliciones=obra_demoliciones,
                    obra_albanileria=obra_albanileria,
                    obra_fontaneria=obra_fontaneria,
                    obra_electricidad=obra_electricidad,
                    obra_carpinteria_interior=obra_carpinteria_interior,
                    obra_carpinteria_exterior=obra_carpinteria_exterior,
                    obra_cocina=obra_cocina,
                    obra_banos=obra_banos,
                    obra_pintura=obra_pintura,
                    obra_otros=obra_otros,
                    cerrajero=cerrajero,
                    alarma=alarma,
                )

    # No refrescar desde BD tras POST

        editable = True
        if proyecto and proyecto.estado and proyecto.estado.lower() in ["cerrado", "cerrado_positivo"]:
            editable = False


    # === CONSOLIDAR CÁLCULO DE FASE (SOLO AQUÍ) ===
    fase = "estudio"
    if proyecto and proyecto.estado:
        fase = proyecto.estado.lower()
    elif request.POST.get("estado"):
        fase = request.POST.get("estado").lower()

    return render(
        request,
        "core/simulador.html",
        {
            "proyectos": proyectos,
            "resultado": resultado,
            "proyecto": proyecto,
            "editable": editable,
            "fase": fase,
        }
    )


from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET

@require_POST
def cambiar_estado_proyecto(request, proyecto_id):
    estado_nuevo = request.POST.get("estado")

    ESTADOS_VALIDOS = [
        "estudio",
        "operacion",
        "cerrado",
        "descartado",
    ]

    proyecto = Proyecto.objects.filter(id=proyecto_id).first()
    if not proyecto:
        return redirect("lista_proyectos")

    if estado_nuevo not in ESTADOS_VALIDOS:
        return redirect("lista_proyectos")

    proyecto.estado = estado_nuevo
    proyecto.save(update_fields=["estado"])

    return redirect("lista_proyectos")




 
# =========================
# AÑADIR INVERSOR A PROYECTO
# =========================
def participacion_create(request, proyecto_id):
    proyecto = Proyecto.objects.filter(id=proyecto_id).first()
    if not proyecto:
        return redirect("lista_proyectos")

    clientes = Cliente.objects.all().order_by("nombre")

    if request.method == "POST":
        cliente_id = request.POST.get("cliente")
        importe = request.POST.get("importe_invertido")

        if cliente_id and importe:
            try:
                importe_val = float(
                    str(importe)
                    .replace(".", "")
                    .replace(",", ".")
                    .replace("€", "")
                    .strip()
                )
            except Exception:
                importe_val = 0

            porcentaje = 0
            if proyecto.precio_compra_inmueble and proyecto.precio_compra_inmueble > 0:
                porcentaje = (importe_val / proyecto.precio_compra_inmueble) * 100

            Participacion.objects.create(
                proyecto=proyecto,
                cliente_id=cliente_id,
                importe_invertido=importe_val,
                porcentaje_participacion=porcentaje,
            )

        return redirect("participacion_create", proyecto_id=proyecto.id)

    participaciones = Participacion.objects.filter(proyecto=proyecto)

    return render(
        request,
        "core/participacion_form.html",
        {
            "proyecto": proyecto,
            "clientes": clientes,
            "participaciones": participaciones,
        },
    )
def lista_proyectos(request):
    estado = request.GET.get("estado")

    # Proyectos (filtrados por estado si se indica)
    proyectos = Proyecto.objects.all().order_by("-id")
    if estado:
        proyectos = proyectos.filter(estado__iexact=estado)

    # Simulaciones que NO están convertidas en proyecto
    simulaciones_pendientes = Simulacion.objects.filter(
        convertida=False
    ).order_by("-id")

    return render(
        request,
        "core/lista_proyectos.html",
        {
            "proyectos": proyectos,
            "simulaciones_pendientes": simulaciones_pendientes,
            "estado_actual": estado,
        },
    )


# Vista clientes
def clientes(request):
    clientes = Cliente.objects.all().order_by("nombre")
    return render(
        request,
        "core/clientes.html",
        {
            "clientes": clientes,
        },
    )



# Nueva vista para crear cliente
def cliente_create(request):
    if request.method == "POST":
        data = request.POST

        Cliente.objects.create(
            tipo_persona=data.get("tipo_persona"),
            nombre=data.get("nombre"),
            dni_cif=data.get("dni_cif"),
            email=data.get("email") or None,
            telefono=data.get("telefono") or None,
            iban=data.get("iban") or None,
            observaciones=data.get("observaciones") or None,
        )

        return redirect("clientes")

    return render(request, "core/clientes_form.html")


# Editar cliente existente
def cliente_edit(request, cliente_id):
    cliente = Cliente.objects.filter(id=cliente_id).first()
    if not cliente:
        return redirect("clientes")

    if request.method == "POST":
        data = request.POST

        cliente.tipo_persona = data.get("tipo_persona")
        cliente.nombre = data.get("nombre")
        cliente.dni_cif = data.get("dni_cif")
        cliente.email = data.get("email") or None
        cliente.telefono = data.get("telefono") or None
        cliente.iban = data.get("iban") or None
        cliente.direccion_postal = data.get("direccion_postal") or None
        cliente.cuota_abonada = True if data.get("cuota_abonada") == "on" else False
        cliente.presente_en_comunidad = True if data.get("presente_en_comunidad") == "on" else False
        cliente.observaciones = data.get("observaciones") or None

        cliente.save()
        return redirect("clientes")

    return render(
        request,
        "core/clientes_form.html",
        {
            "cliente": cliente,
        },
    )


# Vista para importar clientes desde Excel
def clientes_import(request):
    if pd is None:
        messages.error(request, "El módulo pandas no está disponible. No se puede importar el Excel.")
        return redirect("clientes")
    """
    Importa clientes desde un archivo Excel.
    El Excel debe contener como mínimo las columnas:
    nombre, dni_cif

    Columnas opcionales:
    tipo_persona, email, telefono, iban, observaciones
    """

    if request.method == "POST" and request.FILES.get("archivo"):
        archivo = request.FILES["archivo"]

        try:
            df = pd.read_excel(archivo)

            creados = 0
            omitidos = 0

            for _, row in df.iterrows():
                dni_cif = str(row.get("dni_cif", "")).strip()
                nombre = str(row.get("nombre", "")).strip()

                if not dni_cif or not nombre:
                    omitidos += 1
                    continue

                if Cliente.objects.filter(dni_cif=dni_cif).exists():
                    omitidos += 1
                    continue

                Cliente.objects.create(
                    tipo_persona=str(row.get("tipo_persona", "F")).upper()[:1],
                    nombre=nombre,
                    dni_cif=dni_cif,
                    email=row.get("email") or None,
                    telefono=row.get("telefono") or None,
                    iban=row.get("iban") or None,
                    observaciones=row.get("observaciones") or None,
                )
                creados += 1

            messages.success(
                request,
                f"Importación finalizada: {creados} clientes creados, {omitidos} omitidos."
            )

        except Exception as e:
            messages.error(request, f"Error al importar el archivo: {e}")

        return redirect("clientes")

    return render(request, "core/clientes_import.html")
from django.views.decorators.http import require_POST



# === CONVERTIR SIMULACIÓN EN PROYECTO (NUEVA VERSIÓN CORRECTA) ===
from django.views.decorators.http import require_POST

@require_POST
def convertir_simulacion_a_proyecto(request, simulacion_id):
    """
    Convierte una simulación básica en un proyecto real.
    Mapeo correcto de campos:
    - Inmueble (simulación.nombre / direccion) -> Proyecto.direccion
    - Compra (simulación.precio_compra) -> Proyecto.precio_propiedad (precio escritura)
    - Venta (simulación.precio_venta_estimado) -> Proyecto.val_tasacion
    """
    simulacion = Simulacion.objects.filter(
        id=simulacion_id,
        convertida=False
    ).first()

    if not simulacion:
        # No existe o ya convertida: volvemos a proyectos
        return redirect("lista_proyectos")

    # 1) Determinar dirección del inmueble
    direccion = (
        simulacion.direccion
        or simulacion.nombre
        or f"Inmueble simulación #{simulacion.id}"
    )

    # 2) Crear proyecto con los campos correctamente mapeados (bloque exacto con Decimal)
    proyecto = Proyecto.objects.create(
        nombre=f"Proyecto - {direccion}",
        direccion=direccion,
        # Precio de escritura
        precio_propiedad=simulacion.precio_compra,
        # Valor de adquisición (Decimal seguro)
        precio_compra_inmueble=simulacion.precio_compra * Decimal("1.10"),
        # Tasación / valor venta
        val_tasacion=simulacion.precio_venta_estimado,
        roi=simulacion.roi,
        beneficio_neto=simulacion.beneficio,
        estado="estudio",
        simulacion_origen=simulacion,
    )

    # 3) Marcar simulación como convertida (deja de aparecer en pendientes)
    simulacion.convertida = True
    simulacion.save(update_fields=["convertida"])

    # 4) Redirigir al formulario de proyecto (simulador completo)
    return redirect(f"/simulador/?proyecto={proyecto.nombre}")




def simulador_basico(request):
    # Valores por defecto (para que NUNCA se borren)
    direccion = ""
    ref_catastral = ""
    precio_compra_raw = ""
    precio_venta_raw = ""
    resultado = None

    simulacion = None
    if request.method == "POST":
        direccion = request.POST.get("direccion", "")
        ref_catastral = request.POST.get("ref_catastral", "")
        precio_compra_raw = request.POST.get("precio_compra", "")
        precio_venta_raw = request.POST.get("precio_venta", "")

        def parse_euro(valor):
            try:
                return float(
                    str(valor)
                    .replace(".", "")
                    .replace(",", ".")
                    .replace("€", "")
                    .strip()
                )
            except Exception:
                return 0.0

        precio_compra = parse_euro(precio_compra_raw)
        precio_venta = parse_euro(precio_venta_raw)

        beneficio = precio_venta - precio_compra
        roi = (beneficio / precio_compra * 100) if precio_compra > 0 else 0

        resultado = {
            "inversion_total": round(precio_compra, 2),
            "beneficio": round(beneficio, 2),
            "roi": round(roi, 2),
            # REGLA EXACTA QUE PEDISTE
            "viable": beneficio >= 30000 or roi >= 15,
        }

        # Crear simulación en BD con nombre/dirección y todos los campos clave
        simulacion = Simulacion.objects.create(
            nombre=direccion if direccion else None,
            direccion=direccion,
            ref_catastral=ref_catastral,
            precio_compra=precio_compra,
            precio_venta_estimado=precio_venta,
            beneficio=beneficio,
            roi=roi,
            viable=resultado["viable"],
        )

        return render(
            request,
            "core/simulador_basico.html",
            {
                "direccion": direccion,
                "ref_catastral": ref_catastral,
                "precio_compra": precio_compra_raw,
                "precio_venta": precio_venta_raw,
                "resultado": resultado,
                "simulacion": simulacion,
            },
        )

    return render(
        request,
        "core/simulador_basico.html",
        {
            "direccion": direccion,
            "ref_catastral": ref_catastral,
            "precio_compra": precio_compra_raw,
            "precio_venta": precio_venta_raw,
            "resultado": resultado,
        },
    )



from django.http import HttpResponse
from django.views.decorators.http import require_POST

@require_POST
def borrar_simulacion(request, simulacion_id):
    """
    Borrado profesional:
    - Elimina la simulación
    - No redirige
    - Devuelve 204 para uso con fetch/AJAX
    """
    Simulacion.objects.filter(id=simulacion_id).delete()
    return HttpResponse(status=204)


# === Consulta Catastro por Referencia Catastral (GET-compatible endpoint) ===
@require_GET
def obtener_datos_catastro_get(request):
    ref = request.GET.get("ref")

    if not ref:
        return JsonResponse({"error": "Referencia catastral vacía"}, status=400)

    datos = consultar_catastro_por_rc(ref)

    if not datos:
        return JsonResponse({"error": "No se pudo consultar Catastro"}, status=404)

    # 🔒 Guardado temporal en sesión (PASO CLAVE)
    request.session["catastro_tmp"] = {
        "direccion": datos.get("direccion"),
        "lat": datos.get("lat"),
        "lon": datos.get("lon"),
    }

    return JsonResponse(datos)

# === Consulta Catastro por Referencia Catastral (API AJAX) ===
from django.views.decorators.http import require_POST

@require_POST
def obtener_datos_catastro(request):
    ref = request.POST.get("ref_catastral")

    if not ref:
        return JsonResponse({"error": "Referencia catastral vacía"}, status=400)

    datos = consultar_catastro_por_rc(ref)

    if not datos:
        return JsonResponse({"error": "No se pudo consultar Catastro"}, status=404)

    return JsonResponse(datos)