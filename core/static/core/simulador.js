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
   GASTOS DE ADQUISICIÓN AUTOMÁTICOS
=============================== */

function recalcGastosAdquisicion() {
    const escrituraInput = document.querySelector('[name="precio_compra_inmueble"]');
    const itpInput = document.querySelector('[name="itp"]');
    const notariaInput = document.querySelector('[name="notaria"]');
    const mediaValoracionesInput = document.querySelector('[name="media_valoraciones"]');

    const valorEscritura = parseEuro(escrituraInput?.value);

    // ITP: 2% del valor de escritura
    const itp = valorEscritura * 0.02;

    // Notaría: mínimo 500 €, si no 0,20 %
    const notaria = Math.max(500, valorEscritura * 0.002);

    // Media de valoraciones (si existen 3 campos de valoración)
    const valoraciones = [
        parseEuro(document.querySelector('[name="valoracion_1"]')?.value),
        parseEuro(document.querySelector('[name="valoracion_2"]')?.value),
        parseEuro(document.querySelector('[name="valoracion_3"]')?.value)
    ].filter(v => v > 0);

    const mediaValoraciones = valoraciones.length
        ? valoraciones.reduce((a, b) => a + b, 0) / valoraciones.length
        : 0;

    if (itpInput) itpInput.value = formatEuro(itp);
    if (notariaInput) notariaInput.value = formatEuro(notaria);
    if (mediaValoracionesInput) mediaValoracionesInput.value = formatEuro(mediaValoraciones);
}

/* ===============================
   REFORMA (OBRA + SEGURIDAD)
=============================== */


// ===============================
// CÁLCULO SIMPLIFICADO RESULTADOS
// ===============================

function recalcResultados() {
    const compraInput = document.querySelector('[name="precio_compra_inmueble"]');
    const reformaInput = document.querySelector('[name="reforma"]');
    const ventaInput = document.querySelector('[name="precio_venta_estimado"]');
    const beneficioInput = document.querySelector('[name="beneficio"]');
    const roiInput = document.querySelector('[name="roi"]');

    const compra = parseEuro(compraInput?.value);
    const reforma = parseEuro(reformaInput?.value);
    const venta = parseEuro(ventaInput?.value);

    const coste_total = compra + reforma;
    const beneficio = venta - coste_total;
    const roi = coste_total > 0 ? (beneficio / coste_total) * 100 : 0;

    if (beneficioInput) {
        beneficioInput.value = formatEuro(beneficio);
    }
    if (roiInput) {
        roiInput.value = isFinite(roi) ? roi.toFixed(2) : "0.00";
    }
}

/* ===============================
   INIT
=============================== */

document.addEventListener("DOMContentLoaded", () => {
    activarFormatoEuroGlobal();
    aplicarFormatoEuroInicial();
    recalcResultados();
    recalcGastosAdquisicion();

    // Añadir listeners para recalcular resultados y gastos de adquisición
    [
        "precio_compra_inmueble",
        "reforma",
        "precio_venta_estimado",
        "itp",
        "notaria",
        "valoracion_1",
        "valoracion_2",
        "valoracion_3"
    ].forEach(name => {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) {
            el.addEventListener("input", () => {
                recalcResultados();
                recalcGastosAdquisicion();
            });
            el.addEventListener("blur", () => {
                recalcResultados();
                recalcGastosAdquisicion();
            });
        }
    });

    // Limpiar formato euro antes de enviar (solo los campos que quedan)
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", (e) => {
            document.querySelectorAll('[data-euro], .euro-input').forEach(input => {
                input.value = parseEuro(input.value);
            });
        });
    }
});