// Elementos de papelera
const tablaPapelera = document.getElementById("tablaPapelera");
const buscarPapelera = document.getElementById("buscarPapelera");
const btnVaciarPapelera = document.getElementById("btnVaciarPapelera");

const productosEliminados = document.getElementById("productosEliminados");
const ventasAnuladas = document.getElementById("ventasAnuladas");
const totalRegistros = document.getElementById("totalRegistros");


// Actualiza las tarjetas superiores
function actualizarResumenPapelera() {
    const filas = tablaPapelera.querySelectorAll("tr");

    let productos = 0;
    let ventas = 0;

    filas.forEach(function (fila) {
        const tipo = fila.children[0].textContent.trim();

        if (tipo === "Producto") {
            productos += 1;
        }

        if (tipo === "Venta") {
            ventas += 1;
        }
    });

    productosEliminados.textContent = productos;
    ventasAnuladas.textContent = ventas;
    totalRegistros.textContent = filas.length;
}


// Restaura o borra registros
tablaPapelera.addEventListener("click", function (e) {

    if (e.target.classList.contains("btn-restaurar")) {
        const fila = e.target.closest("tr");
        fila.remove();

        actualizarResumenPapelera();
        alert("Registro restaurado correctamente.");
    }

    if (e.target.classList.contains("btn-borrar")) {
        const confirmar = confirm("¿Seguro que deseas borrar este registro?");

        if (confirmar) {
            const fila = e.target.closest("tr");
            fila.remove();

            actualizarResumenPapelera();
            alert("Registro borrado visualmente.");
        }
    }

});


// Busca registros
buscarPapelera.addEventListener("input", function () {
    const texto = buscarPapelera.value.toLowerCase();
    const filas = tablaPapelera.querySelectorAll("tr");

    filas.forEach(function (fila) {
        const contenido = fila.textContent.toLowerCase();

        if (contenido.includes(texto)) {
            fila.style.display = "";
        } else {
            fila.style.display = "none";
        }
    });
});


// Vacía la papelera completa
btnVaciarPapelera.addEventListener("click", function () {
    const confirmar = confirm("¿Seguro que deseas vaciar la papelera?");

    if (confirmar) {
        tablaPapelera.innerHTML = "";
        actualizarResumenPapelera();
        alert("Papelera vaciada correctamente.");
    }
});