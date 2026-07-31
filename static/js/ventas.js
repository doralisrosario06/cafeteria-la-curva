document.addEventListener("DOMContentLoaded", function () {
    const tarjetasProductos = document.querySelectorAll(".product-card");
    const botonesCategorias = document.querySelectorAll(".category");

    const buscarProducto = document.getElementById("buscarProducto");
    const carritoLista = document.getElementById("carritoLista");

    const subtotalTexto = document.getElementById("subtotalTexto");
    const totalTexto = document.getElementById("totalTexto");
    const cambioTexto = document.getElementById("cambioTexto");

    const efectivoRecibido = document.getElementById("efectivoRecibido");
    const btnFinalizarVenta = document.getElementById("btnFinalizarVenta");
    const btnLimpiar = document.getElementById("btnLimpiar");

    const modalTamano = document.getElementById("modalTamano");
    const productoTamano = document.getElementById("productoTamano");
    const opcionesPresentacion = document.getElementById(
        "opcionesPresentacion"
    );
    const btnCerrarModal = document.getElementById("btnCerrarModal");

    const tipoPago = document.getElementById("tipoPago");
    const camposEfectivo = document.getElementById("camposEfectivo");
    const camposFiado = document.getElementById("camposFiado");

    const nombreClienteFiado = document.getElementById(
        "nombreClienteFiado"
    );
    const telefonoClienteFiado = document.getElementById(
        "telefonoClienteFiado"
    );
    const abonoInicial = document.getElementById("abonoInicial");

    const totalFiadoTexto = document.getElementById(
        "totalFiadoTexto"
    );
    const abonoFiadoTexto = document.getElementById(
        "abonoFiadoTexto"
    );
    const pendienteFiadoTexto = document.getElementById(
        "pendienteFiadoTexto"
    );

    let carrito = [];
    let productoSeleccionado = null;
    let categoriaActual = "Todos";

    // Formatea una cantidad como dinero dominicano
    function formatearDinero(valor) {
        return `RD$ ${Number(valor).toFixed(2)}`;
    }

    // Calcula el total actual del carrito
    function calcularTotal() {
        return carrito.reduce(function (acumulado, item) {
            return acumulado + item.precio * item.cantidad;
        }, 0);
    }

    // Actualiza el cambio de una venta en efectivo
    function actualizarCambio() {
        const total = calcularTotal();
        const efectivo = Number(efectivoRecibido.value) || 0;
        const cambio = efectivo >= total ? efectivo - total : 0;

        cambioTexto.textContent = formatearDinero(cambio);
    }

    // Actualiza el resumen visual de una venta fiada
    function actualizarResumenFiado() {
        const total = calcularTotal();
        let abono = Number(abonoInicial.value) || 0;

        if (abono < 0) {
            abono = 0;
            abonoInicial.value = "0";
        }

        if (abono > total) {
            abono = total;
            abonoInicial.value = total.toFixed(2);
        }

        const pendiente = total - abono;

        totalFiadoTexto.textContent = formatearDinero(total);
        abonoFiadoTexto.textContent = formatearDinero(abono);
        pendienteFiadoTexto.textContent = formatearDinero(pendiente);
    }

    // Muestra los campos correspondientes a la forma de pago
    function actualizarFormaPago() {
        if (tipoPago.value === "Fiado") {
            camposEfectivo.style.display = "none";
            camposFiado.style.display = "block";

            efectivoRecibido.value = "";
            cambioTexto.textContent = formatearDinero(0);

            actualizarResumenFiado();
        } else {
            camposEfectivo.style.display = "block";
            camposFiado.style.display = "none";

            nombreClienteFiado.value = "";
            telefonoClienteFiado.value = "";
            abonoInicial.value = "0";

            actualizarCambio();
        }
    }

    // Dibuja nuevamente los productos del carrito
    function mostrarCarrito() {
        carritoLista.innerHTML = "";

        if (carrito.length === 0) {
            carritoLista.innerHTML = `
                <p class="text-muted">
                    No hay productos agregados.
                </p>
            `;
        } else {
            carrito.forEach(function (item, indice) {
                const fila = document.createElement("div");
                fila.className = "cart-item";

                fila.innerHTML = `
                    <div>
                        <strong>${item.nombre}</strong>

                        <small>
                            ${item.presentacion_nombre}
                            · ${item.cantidad}
                            × ${formatearDinero(item.precio)}
                        </small>
                    </div>

                    <div class="cart-actions">
                        <strong>
                            ${formatearDinero(
                                item.precio * item.cantidad
                            )}
                        </strong>

                        <button
                            type="button"
                            data-indice="${indice}"
                            title="Eliminar producto">
                            ×
                        </button>
                    </div>
                `;

                carritoLista.appendChild(fila);
            });
        }

        const total = calcularTotal();

        subtotalTexto.textContent = formatearDinero(total);
        totalTexto.textContent = formatearDinero(total);

        actualizarCambio();
        actualizarResumenFiado();

        const botonesEliminar = carritoLista.querySelectorAll(
            ".cart-actions button"
        );

        botonesEliminar.forEach(function (boton) {
            boton.addEventListener("click", function () {
                const indice = Number(boton.dataset.indice);

                carrito.splice(indice, 1);
                mostrarCarrito();
            });
        });
    }

    // Agrega al carrito la presentación seleccionada
    function agregarAlCarrito(presentacion) {
        if (!productoSeleccionado) {
            return;
        }

        const stock = Number(productoSeleccionado.stock) || 0;

        const cantidadActual = carrito
            .filter(function (item) {
                return (
                    item.producto_id === productoSeleccionado.id
                );
            })
            .reduce(function (total, item) {
                return total + item.cantidad;
            }, 0);

        if (cantidadActual >= stock) {
            alert("No hay suficiente existencia de este producto.");
            return;
        }

        const existente = carrito.find(function (item) {
            return (
                item.producto_id === productoSeleccionado.id &&
                item.presentacion_id === presentacion.id
            );
        });

        if (existente) {
            existente.cantidad += 1;
        } else {
            carrito.push({
                producto_id: productoSeleccionado.id,
                nombre: productoSeleccionado.nombre,
                presentacion_id: presentacion.id,
                presentacion_nombre: presentacion.nombre,
                precio: Number(presentacion.precio),
                cantidad: 1
            });
        }

        cerrarModal();
        mostrarCarrito();
    }

    // Abre la ventana para elegir una presentación
    function abrirModal(producto) {
        productoSeleccionado = producto;

        productoTamano.textContent = producto.nombre;
        opcionesPresentacion.innerHTML = "";

        if (producto.presentaciones.length === 0) {
            opcionesPresentacion.innerHTML = `
                <p class="text-muted">
                    Este producto no tiene presentaciones.
                </p>
            `;

            modalTamano.classList.add("active");
            return;
        }

        producto.presentaciones.forEach(function (presentacion) {
            const boton = document.createElement("button");

            boton.type = "button";
            boton.className = "btn-opcion";

            boton.textContent =
                `${presentacion.nombre} · ` +
                formatearDinero(presentacion.precio);

            boton.addEventListener("click", function () {
                agregarAlCarrito(presentacion);
            });

            opcionesPresentacion.appendChild(boton);
        });

        modalTamano.classList.add("active");
    }

    // Cierra la ventana de presentaciones
    function cerrarModal() {
        modalTamano.classList.remove("active");
        productoSeleccionado = null;
    }

    // Filtra los productos por nombre y categoría
    function filtrarProductos() {
        const texto = buscarProducto.value
            .trim()
            .toLowerCase();

        tarjetasProductos.forEach(function (tarjeta) {
            const nombre = tarjeta.dataset.nombre.toLowerCase();
            const categoria = tarjeta.dataset.categoria;

            const coincideNombre = nombre.includes(texto);

            const coincideCategoria =
                categoriaActual === "Todos" ||
                categoria === categoriaActual;

            tarjeta.style.display =
                coincideNombre && coincideCategoria
                    ? ""
                    : "none";
        });
    }

    // Limpia todos los datos de la venta actual
    function limpiarVenta() {
        carrito = [];

        efectivoRecibido.value = "";
        nombreClienteFiado.value = "";
        telefonoClienteFiado.value = "";
        abonoInicial.value = "0";

        tipoPago.value = "Efectivo";

        mostrarCarrito();
        actualizarFormaPago();
    }

    // Procesa y envía la venta a Flask
    async function finalizarVenta() {
        if (carrito.length === 0) {
            alert("Debes agregar productos a la venta.");
            return;
        }

        const total = calcularTotal();
        const formaPago = tipoPago.value;

        let efectivo = 0;
        let nombreCliente = "";
        let telefonoCliente = "";
        let abono = 0;

        if (formaPago === "Efectivo") {
            efectivo = Number(efectivoRecibido.value) || 0;

            if (efectivo <= 0) {
                alert("Escribe el efectivo recibido.");
                efectivoRecibido.focus();
                return;
            }

            if (efectivo < total) {
                alert("El efectivo recibido no alcanza.");
                efectivoRecibido.focus();
                return;
            }
        } else {
            nombreCliente = nombreClienteFiado.value.trim();
            telefonoCliente = telefonoClienteFiado.value.trim();
            abono = Number(abonoInicial.value) || 0;

            if (!nombreCliente) {
                alert(
                    "Debes escribir el nombre del cliente."
                );
                nombreClienteFiado.focus();
                return;
            }

            if (abono < 0) {
                alert("El abono no puede ser negativo.");
                abonoInicial.focus();
                return;
            }

            if (abono > total) {
                alert(
                    "El abono no puede superar el total de la venta."
                );
                abonoInicial.focus();
                return;
            }
        }

        btnFinalizarVenta.disabled = true;
        btnFinalizarVenta.textContent = "Guardando...";

        try {
            const respuesta = await fetch("/ventas/finalizar", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    carrito: carrito,
                    tipo_pago: formaPago,
                    efectivo: efectivo,
                    nombre_cliente: nombreCliente,
                    telefono: telefonoCliente,
                    abono_inicial: abono
                })
            });

            const resultado = await respuesta.json();

            if (!respuesta.ok || !resultado.ok) {
                alert(
                    resultado.mensaje ||
                    "No se pudo guardar la venta."
                );
                return;
            }

            if (formaPago === "Fiado") {
                alert(
                    "Venta fiada registrada correctamente.\n\n" +
                    "Cliente: " + nombreCliente + "\n" +
                    "Total: " +
                    formatearDinero(resultado.total) + "\n" +
                    "Abono: " +
                    formatearDinero(resultado.abono) + "\n" +
                    "Pendiente: " +
                    formatearDinero(resultado.pendiente)
                );
            } else {
                alert(
                    "Venta realizada correctamente.\n\n" +
                    "Factura: #" + resultado.venta_id + "\n" +
                    "Total: " +
                    formatearDinero(resultado.total) + "\n" +
                    "Cambio: " +
                    formatearDinero(resultado.cambio)
                );
            }

            limpiarVenta();

            // Recarga para mostrar el stock actualizado
            window.location.reload();
        } catch (error) {
            console.error(error);

            alert(
                "No fue posible conectar con el servidor."
            );
        } finally {
            btnFinalizarVenta.disabled = false;
            btnFinalizarVenta.textContent = "Finalizar venta";
        }
    }

    tarjetasProductos.forEach(function (tarjeta) {
        tarjeta.addEventListener("click", function () {
            const stock = Number(tarjeta.dataset.stock) || 0;

            if (stock <= 0) {
                alert("Este producto está agotado.");
                return;
            }

            let presentaciones = [];

            try {
                presentaciones = JSON.parse(
                    tarjeta.dataset.presentaciones
                );
            } catch (error) {
                console.error(
                    "Error leyendo presentaciones:",
                    error
                );

                alert(
                    "No se pudieron leer las presentaciones."
                );
                return;
            }

            abrirModal({
                id: Number(tarjeta.dataset.id),
                nombre: tarjeta.dataset.nombre,
                stock: stock,
                presentaciones: presentaciones.map(
                    function (presentacion) {
                        return {
                            id: Number(presentacion.id),
                            nombre: presentacion.nombre,
                            precio: Number(presentacion.precio)
                        };
                    }
                )
            });
        });
    });

    botonesCategorias.forEach(function (boton) {
        boton.addEventListener("click", function () {
            botonesCategorias.forEach(function (otroBoton) {
                otroBoton.classList.remove("active");
            });

            boton.classList.add("active");
            categoriaActual = boton.dataset.categoria;

            filtrarProductos();
        });
    });

    buscarProducto.addEventListener(
        "input",
        filtrarProductos
    );

    efectivoRecibido.addEventListener(
        "input",
        actualizarCambio
    );

    abonoInicial.addEventListener(
        "input",
        actualizarResumenFiado
    );

    tipoPago.addEventListener(
        "change",
        actualizarFormaPago
    );

    btnCerrarModal.addEventListener(
        "click",
        cerrarModal
    );

    modalTamano.addEventListener("click", function (evento) {
        if (evento.target === modalTamano) {
            cerrarModal();
        }
    });

    btnLimpiar.addEventListener(
        "click",
        limpiarVenta
    );

    btnFinalizarVenta.addEventListener(
        "click",
        finalizarVenta
    );

    mostrarCarrito();
    actualizarFormaPago();
});