// Formulario de configuración
const formConfiguracion = document.getElementById("formConfiguracion");

const nombreNegocio = document.getElementById("nombre_negocio");
const telefono = document.getElementById("telefono");
const moneda = document.getElementById("moneda");
const estado = document.getElementById("estado");

const previewNombre = document.getElementById("previewNombre");
const previewTelefono = document.getElementById("previewTelefono");
const previewMoneda = document.getElementById("previewMoneda");
const previewEstado = document.getElementById("previewEstado");


// Guarda visualmente la configuración
formConfiguracion.addEventListener("submit", function (e) {
    e.preventDefault();

    previewNombre.textContent = nombreNegocio.value;

    if (telefono.value.trim() === "") {
        previewTelefono.textContent = "Teléfono no registrado";
    } else {
        previewTelefono.textContent = "Teléfono: " + telefono.value;
    }

    previewMoneda.textContent = "Moneda: " + moneda.value;
    previewEstado.textContent = "Estado: " + estado.value;

    alert("Configuración guardada correctamente.");
});


// Usuarios visuales
const btnMostrarUsuario = document.getElementById("btnMostrarUsuario");
const formUsuario = document.getElementById("formUsuario");
const tablaUsuarios = document.getElementById("tablaUsuarios");


// Muestra u oculta el formulario de usuario
btnMostrarUsuario.addEventListener("click", function () {
    if (formUsuario.style.display === "none") {
        formUsuario.style.display = "grid";
    } else {
        formUsuario.style.display = "none";
    }
});


// Agrega usuario visualmente
formUsuario.addEventListener("submit", function (e) {
    e.preventDefault();

    const nombre = document.getElementById("nombre_usuario").value;
    const usuario = document.getElementById("usuario_login").value;
    const rol = document.getElementById("rol_usuario").value;

    if (nombre.trim() === "" || usuario.trim() === "") {
        alert("Completa el nombre y el usuario.");
        return;
    }

    const fila = document.createElement("tr");

    fila.innerHTML = `
        <td>${nombre}</td>
        <td>${usuario}</td>
        <td>${rol}</td>
        <td>
            <span class="badge-ok">Activo</span>
        </td>
        <td>
            <button type="button" class="btn-small btn-desactivar">
                Desactivar
            </button>
        </td>
    `;

    tablaUsuarios.appendChild(fila);

    formUsuario.reset();
    formUsuario.style.display = "none";

    alert("Usuario agregado visualmente.");
});


// Activa o desactiva usuarios visualmente
tablaUsuarios.addEventListener("click", function (e) {
    if (e.target.classList.contains("btn-desactivar")) {
        const fila = e.target.closest("tr");
        const estadoUsuario = fila.querySelector("td:nth-child(4)");
        const boton = e.target;

        if (boton.textContent.trim() === "Desactivar") {
            estadoUsuario.innerHTML = '<span class="badge-danger">Inactivo</span>';
            boton.textContent = "Activar";
        } else {
            estadoUsuario.innerHTML = '<span class="badge-ok">Activo</span>';
            boton.textContent = "Desactivar";
        }
    }
});