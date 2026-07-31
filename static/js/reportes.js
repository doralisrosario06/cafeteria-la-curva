const btnImprimirReporte = document.getElementById("btnImprimirReporte");
const btnExportarExcel = document.getElementById("btnExportarExcel");

if (btnImprimirReporte) {
    btnImprimirReporte.addEventListener("click", function () {
        window.print();
    });
}

if (btnExportarExcel) {
    btnExportarExcel.addEventListener("click", function () {
        const tabla = document.getElementById("tablaFacturas");
        let contenido = "ID,Fecha,Total,Efectivo,Cambio\n";

        const filas = tabla.querySelectorAll("tbody > tr");

        filas.forEach(function (fila) {
            const columnas = fila.querySelectorAll("td");

            if (columnas.length >= 5) {
                contenido += [
                    columnas[0].textContent.trim(),
                    columnas[1].textContent.trim(),
                    columnas[2].textContent.trim(),
                    columnas[3].textContent.trim(),
                    columnas[4].textContent.trim()
                ].join(",") + "\n";
            }
        });

        const archivo = new Blob([contenido], {
            type: "text/csv;charset=utf-8;"
        });

        const enlace = document.createElement("a");
        enlace.href = URL.createObjectURL(archivo);
        enlace.download = "facturas_cafeteria_la_curva.csv";
        enlace.click();
    });
}