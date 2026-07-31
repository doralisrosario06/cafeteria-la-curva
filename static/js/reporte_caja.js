const btnImprimirCaja = document.getElementById("btnImprimirCaja");
const btnExportarCaja = document.getElementById("btnExportarCaja");

if (btnImprimirCaja) {
    btnImprimirCaja.addEventListener("click", function () {
        window.print();
    });
}

if (btnExportarCaja) {
    btnExportarCaja.addEventListener("click", function () {
        const tabla = document.getElementById("tablaResumenCaja");
        let contenido = "Fecha,Monto inicial,Ventas,Entradas,Salidas,Total esperado,Dinero contado,Diferencia\n";

        const filas = tabla.querySelectorAll("tbody tr");

        filas.forEach(function (fila) {
            const columnas = fila.querySelectorAll("td");
            let datos = [];

            columnas.forEach(function (columna) {
                datos.push(columna.textContent.trim());
            });

            contenido += datos.join(",") + "\n";
        });

        const archivo = new Blob([contenido], {
            type: "text/csv;charset=utf-8;"
        });

        const enlace = document.createElement("a");
        enlace.href = URL.createObjectURL(archivo);
        enlace.download = "reporte_caja_la_curva.csv";
        enlace.click();
    });
}