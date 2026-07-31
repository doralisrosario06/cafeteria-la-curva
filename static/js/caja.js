// Elementos principales de la caja
const btnAbrirCaja = document.getElementById("btnAbrirCaja");
const btnCerrarCaja = document.getElementById("btnCerrarCaja");
const formMovimiento = document.getElementById("formMovimiento");
const tablaMovimientos = document.getElementById("tablaMovimientos");

const cajaActual = document.getElementById("cajaActual");
const totalSalidasTexto = document.getElementById("totalSalidas");

let cajaAbierta = false;
let totalCaja = 0;
let totalSalidas = 0;


// Actualiza los totales en pantalla
function actualizarTotales() {
    cajaActual.textContent = "RD$ " + totalCaja.toFixed(2);
    totalSalidasTexto.textContent = "RD$ " + totalSalidas.toFixed(2);
}


// Agrega un movimiento a la tabla
function agregarMovimiento(concepto, descripcion, tipo, monto) {
    const hora = new Date().toLocaleTimeString();

    const clase = tipo === "Entrada" ? "badge-ok" : "badge-danger";

    const fila = document.createElement("tr");

    fila.innerHTML = `
        <td>${hora}</td>
        <td>${concepto}</td>
        <td>${descripcion}</td>
        <td><span class="${clase}">${tipo}</span></td>
        <td>RD$ ${monto.toFixed(2)}</td>
    `;

    tablaMovimientos.appendChild(fila);
}


// Abre la caja
btnAbrirCaja.addEventListener("click", function () {
    const montoInicial = Number(document.getElementById("monto_inicial").value);

    if (cajaAbierta) {
        alert("La caja ya está abierta.");
        return;
    }

    if (montoInicial <= 0) {
        alert("Escribe un monto inicial válido.");
        return;
    }

    cajaAbierta = true;
    totalCaja = montoInicial;

    agregarMovimiento("Apertura", "Monto inicial del día", "Entrada", montoInicial);
    actualizarTotales();

    alert("Caja abierta correctamente.");
});


// Guarda entradas y salidas
formMovimiento.addEventListener("submit", function (e) {
    e.preventDefault();

    if (!cajaAbierta) {
        alert("Primero debes abrir la caja.");
        return;
    }

    const tipo = document.getElementById("tipo_movimiento").value;
    const concepto = document.getElementById("concepto").value;
    const descripcion = document.getElementById("descripcion").value;
    const monto = Number(document.getElementById("monto").value);

    if (monto <= 0) {
        alert("Escribe un monto válido.");
        return;
    }

    if (tipo === "Entrada") {
        totalCaja += monto;
    } else {
        totalCaja -= monto;
        totalSalidas += monto;
    }

    agregarMovimiento(concepto, descripcion, tipo, monto);
    actualizarTotales();

    formMovimiento.reset();
});


// Cierra la caja
btnCerrarCaja.addEventListener("click", function () {
    const montoContado = Number(document.getElementById("monto_final").value);

    if (!cajaAbierta) {
        alert("La caja no está abierta.");
        return;
    }

    if (montoContado < 0 || document.getElementById("monto_final").value === "") {
        alert("Escribe el dinero contado.");
        return;
    }

    const diferencia = montoContado - totalCaja;

    cajaAbierta = false;

    alert(
        "Caja cerrada.\n" +
        "Total esperado: RD$ " + totalCaja.toFixed(2) + "\n" +
        "Dinero contado: RD$ " + montoContado.toFixed(2) + "\n" +
        "Diferencia: RD$ " + diferencia.toFixed(2)
    );
});