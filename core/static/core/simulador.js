/* ===============================
   UTILIDADES MONETARIAS
=============================== */

function parseEuro(value) {
    if (!value) return 0;
    return Number(
        value.toString()
            .replace(/\./g, "")
            .replace(",", ".")
            .replace("€", "")
            .trim()
    ) || 0;
}

function formatEuro(value) {
    if (value === null || value === "" || isNaN(value)) return "";
    return new Intl.NumberFormat("es-ES", {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function activarFormatoEuroGlobal() {
    document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
        input.addEventListener("blur", () => {
            input.value = formatEuro(parseEuro(input.value));
        });
    });
}

function aplicarFormatoEuroInicial() {
    document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
        const valor = parseEuro(input.value);
        if (valor) {
            input.value = formatEuro(valor);
        }
    });
}

/* ===============================
   CÁLCULOS
=============================== */

/* ===============================
   REFORMA (OBRA + SEGURIDAD)
=============================== */

function recalcReforma() {
    const camposReforma = [
        // OBRA 4A
        "obra_demoliciones",
        "obra_albanileria",
        "obra_fontaneria",
        "obra_electricidad",
        "obra_carpinteria_interior",
        "obra_carpinteria_exterior",
        "obra_cocina",
        "obra_banos",
        "obra_pintura",
        "obra_otros",

        // SEGURIDAD 4B
        "seguridad_cerrajero",
        "seguridad_alarma"
    ];

    let total = 0;

    camposReforma.forEach(name => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            total += parseEuro(el.value);
        }
    });

    const reformaInput = document.querySelector('[name="reforma"]');
    if (reformaInput && !reformaInput.dataset.manual) {
        reformaInput.value = formatEuro(total);
    }
}

function recalcMediaValoraciones() {
    const campos = [
        "val_idealista",
        "val_fotocasa",
        "val_registradores",
        "val_casafari",
        "val_tasacion"
    ];

    let total = 0;
    let count = 0;

    campos.forEach(name => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            const v = parseEuro(el.value);
            if (v > 0) {
                total += v;
                count++;
            }
        }
    });

    const media = count > 0 ? total / count : 0;

    const mediaInput = document.querySelector('[name="media_valoraciones"]');
    if (mediaInput) mediaInput.value = formatEuro(media);

    const venta = document.querySelector('[name="precio_venta_estimado"]');
    if (venta && !venta.dataset.manual) {
        venta.value = formatEuro(media);
    }
}

function recalcPrecioCompraInmueble() {
    const escritura = parseEuro(document.querySelector('[name="precio_propiedad"]')?.value);

    const notariaEl = document.querySelector('[name="notaria"]');
    const registroEl = document.querySelector('[name="registro"]');
    const itpEl = document.querySelector('[name="itp"]');
    const otrosEl = document.querySelector('[name="otros_gastos_compra"]');

    // Autocalcular gastos básicos si no son manuales
    if (notariaEl && !notariaEl.dataset.manual) {
        notariaEl.value = formatEuro(Math.max(escritura * 0.002, 500));
    }
    if (registroEl && !registroEl.dataset.manual) {
        registroEl.value = formatEuro(Math.max(escritura * 0.002, 500));
    }
    if (itpEl && !itpEl.dataset.manual) {
        itpEl.value = formatEuro(escritura * 0.02);
    }

    const notaria = parseEuro(notariaEl?.value);
    const registro = parseEuro(registroEl?.value);
    const itp = parseEuro(itpEl?.value);
    const otros = parseEuro(otrosEl?.value);

    const totalAdquisicion = escritura + notaria + registro + itp + otros;

    const totalInput = document.querySelector('[name="precio_compra_inmueble"]');
    if (totalInput) {
        totalInput.value = formatEuro(totalAdquisicion);
    }
}

/* ===============================
   MAPA
=============================== */

function activarMapaAutomatico() {
    const iframe = document.getElementById("mapIframe");
    const direccionInput = document.getElementById("direccion");

    if (!iframe || !direccionInput) return;

    const direccion = direccionInput.value?.trim();
    if (!direccion) return;

    iframe.src = `https://www.google.com/maps?q=${encodeURIComponent(direccion)}&output=embed`;
}

/* ===============================
   CATASTRO
=============================== */

function abrirCatastro() {
    const refInput =
        document.querySelector('[name="ref_catastral"]') ||
        document.getElementById("ref_catastral");

    if (!refInput || !refInput.value.trim()) {
        alert("Introduce una referencia catastral válida.");
        return;
    }

    const ref = refInput.value.trim();
    const url = `/catastro/obtener/?ref=${encodeURIComponent(ref)}`;
    window.open(url, "_blank");
}

/* ===============================
   CONTROL BOTÓN CATASTRO
=============================== */

function controlarBotonCatastro() {
    const refInput =
        document.querySelector('[name="ref_catastral"]') ||
        document.getElementById("ref_catastral");
    const btnCatastro = document.getElementById("btnCatastro");

    if (!refInput || !btnCatastro) return;

    const toggle = () => {
        const activa = refInput.value.trim().length > 0;
        btnCatastro.disabled = !activa;
        btnCatastro.style.opacity = activa ? "1" : "0.5";
        btnCatastro.style.cursor = activa ? "pointer" : "not-allowed";
    };

    refInput.addEventListener("input", toggle);
    refInput.addEventListener("blur", toggle);
    toggle();
}

/* ===============================
   INIT
=============================== */

document.addEventListener("DOMContentLoaded", () => {

    activarFormatoEuroGlobal();
    recalcMediaValoraciones();
    // ===============================
    // REACCIONAR A CAMBIOS EN VALORACIONES
    // ===============================
    [
        "val_idealista",
        "val_fotocasa",
        "val_registradores",
        "val_casafari",
        "val_tasacion"
    ].forEach(name => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            el.addEventListener("input", recalcMediaValoraciones);
            el.addEventListener("blur", recalcMediaValoraciones);
        }
    });
    recalcPrecioCompraInmueble();
    [
        "precio_propiedad",
        "notaria",
        "registro",
        "itp",
        "otros_gastos_compra"
    ].forEach(name => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            el.addEventListener("input", recalcPrecioCompraInmueble);
            el.addEventListener("blur", recalcPrecioCompraInmueble);
        }
    });
    activarMapaAutomatico();
    aplicarFormatoEuroInicial();

    document.querySelectorAll('[data-euro], .euro-input').forEach(el => {
        const name = el.getAttribute("name") || "";
        const esValoracion = [
            "val_idealista",
            "val_fotocasa",
            "val_registradores",
            "val_casafari",
            "val_tasacion"
        ].includes(name);

        if (!esValoracion) {
            el.addEventListener("input", () => el.dataset.manual = "1");
        }
    });

    const direccion = document.getElementById("direccion");
    if (direccion) {
        direccion.addEventListener("input", activarMapaAutomatico);
        direccion.addEventListener("blur", activarMapaAutomatico);
    }

    // Recalcular reforma cuando se modifique obra o seguridad
    [
        "obra_demoliciones",
        "obra_albanileria",
        "obra_fontaneria",
        "obra_electricidad",
        "obra_carpinteria_interior",
        "obra_carpinteria_exterior",
        "obra_cocina",
        "obra_banos",
        "obra_pintura",
        "obra_otros",
        "seguridad_cerrajero",
        "seguridad_alarma"
    ].forEach(name => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            el.addEventListener("input", recalcReforma);
            el.addEventListener("blur", recalcReforma);
        }
    });

    // Cálculo inicial
    recalcReforma();

    // Restaurar valores guardados en sessionStorage tras reload
    document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
        if (input.name) {
            const saved = sessionStorage.getItem("sim_" + input.name);
            if (saved !== null) {
                input.value = saved;
            }
        }
    });

    recalcMediaValoraciones();
    recalcReforma();

    // ===============================
    // LIMPIAR FORMATO € ANTES DE ENVIAR
    // ===============================
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", (e) => {
            document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
                if (input.name) {
                    sessionStorage.setItem("sim_" + input.name, input.value);
                }
            });

            const valoresVisibles = {};
            document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
                valoresVisibles[input.name] = input.value;
            });

            document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
                const name = input.getAttribute("name") || "";
                const esValoracion = [
                    "val_idealista",
                    "val_fotocasa",
                    "val_registradores",
                    "val_casafari",
                    "val_tasacion",
                    "media_valoraciones"
                ].includes(name);

                if (!esValoracion) {
                    input.value = parseEuro(input.value);
                }
            });

            setTimeout(() => {
                document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
                    if (valoresVisibles[input.name] !== undefined) {
                        input.value = valoresVisibles[input.name];
                    }
                });
                recalcMediaValoraciones();
                recalcReforma();
            }, 0);
        });
    }

    controlarBotonCatastro();
});