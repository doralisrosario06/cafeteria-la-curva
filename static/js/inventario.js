// Formulario de productos
const formProducto = document.getElementById("formProducto");
const tablaInventario = document.getElementById("tablaInventario");
const buscarInventario = document.getElementById("buscarInventario");

// Agrega producto a la tabla
formProducto.addEventListener("submit", function (e) {
    e.preventDefault();

    const nombre = document.getElementById("nombre").value;
    const categoria = document.getElementById("categoria").value;
    const compra = Number(document.getElementById("compra").value);
    const stock = Number(document.getElementById("stock").value);

    const estado = stock > 0 ? "Disponible" : "Agotado";
    const claseEstado = stock > 0 ? "badge-ok" : "badge-danger";

    const fila = document.createElement("tr");

    fila.innerHTML = `
        <td>${nombre}</td>
        <td>${categoria}</td>
        <td>RD$ ${compra.toFixed(2)}</td>
        <td>${stock}</td>
        <td><span class="${claseEstado}">${estado}</span></td>
        <td>
            <button type="button" class="btn-small danger btn-eliminar">Eliminar</button>
        </td>
    `;

    tablaInventario.appendChild(fila);
    formProducto.reset();
});

// Elimina producto visualmente
tablaInventario.addEventListener("click", function (e) {
    if (e.target.classList.contains("btn-eliminar")) {
        e.target.closest("tr").remove();
    }
});

// Busca productos en la tabla
buscarInventario.addEventListener("input", function () {
    const texto = buscarInventario.value.toLowerCase();
    const filas = tablaInventario.querySelectorAll("tr");

    filas.forEach(function (fila) {
        const contenido = fila.textContent.toLowerCase();

        if (contenido.includes(texto)) {
            fila.style.display = "";
        } else {
            fila.style.display = "none";
        }
    });
});