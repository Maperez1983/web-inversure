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

function getFieldByNames(names) {
    for (const name of names) {
        const el = document.querySelector(`[name="${name}"]`);
        if (el) return el;
    }
    return null;
}

/* ===============================
   GASTOS DE ADQUISICIÓN
=============================== */
function recalcGastosAdquisicion() {
    const escrituraInput = getFieldByNames([
        "precio_escritura",
        "precio_compra_inmueble",
        "precio_compra",
        "valor_escritura"
    ]);

    const itpInput = getFieldByNames(["itp", "gasto_itp"]);
    const notariaInput = getFieldByNames(["notaria", "gasto_notaria"]);
    const registroInput = getFieldByNames(["registro", "gasto_registro"]);

    const valorEscritura = parseEuro(escrituraInput?.value);

    const itp = valorEscritura * 0.02;
    const notaria = Math.max(500, valorEscritura * 0.002);
    const registro = Math.max(500, valorEscritura * 0.002);

    if (itpInput) itpInput.value = formatEuro(itp);
    if (notariaInput) notariaInput.value = formatEuro(notaria);
    if (registroInput) registroInput.value = formatEuro(registro);

    let otros = 0;
    ["gestoria", "tasacion", "comision_agencia", "otros_gastos"].forEach(n => {
        const el = getFieldByNames([n]);
        if (el) otros += parseEuro(el.value);
    });

    const valorAdquisicion = valorEscritura + itp + notaria + registro + otros;

    const valorAdquisicionInput = getFieldByNames([
        "valor_adquisicion",
        "valor_adquisicion_total",
        "valor_adquisicion_inmueble"
    ]);

    if (valorAdquisicionInput) {
        valorAdquisicionInput.value = formatEuro(valorAdquisicion);
    }
}

/* ===============================
   RESULTADOS / RENTABILIDAD
=============================== */
function recalcResultados() {
    const valorAdqInput = getFieldByNames([
        "valor_adquisicion",
        "valor_adquisicion_total",
        "valor_adquisicion_inmueble"
    ]);

    const reformaInput = getFieldByNames(["reforma", "coste_reforma"]);
    const ventaInput = getFieldByNames(["precio_venta_estimado", "venta_estimada", "media_valoraciones"]);
    const beneficioInput = getFieldByNames(["beneficio"]);
    const roiInput = getFieldByNames(["roi"]);

    const valorAdq = parseEuro(valorAdqInput?.value);
    const reforma = parseEuro(reformaInput?.value);
    const venta = parseEuro(ventaInput?.value);

    const costeTotal = valorAdq + reforma;
    const beneficio = venta - costeTotal;
    const roi = costeTotal > 0 ? (beneficio / costeTotal) * 100 : 0;

    if (beneficioInput) beneficioInput.value = formatEuro(beneficio);
    if (roiInput) roiInput.value = isFinite(roi) ? roi.toFixed(2) : "0.00";
}

/* ===============================
   INIT
=============================== */
document.addEventListener("DOMContentLoaded", () => {
    recalcGastosAdquisicion();
    recalcResultados();

    document.querySelectorAll("input").forEach(el => {
        el.addEventListener("input", () => {
            recalcGastosAdquisicion();
            recalcResultados();
        });
    });
});