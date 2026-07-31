// Gráfica principal de ganancias
const graficaGanancias = document.getElementById("graficaGanancias");

if (graficaGanancias) {
    new Chart(graficaGanancias, {
        type: "bar",
        data: {
            labels: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
            datasets: [
                {
                    label: "Ingresos",
                    data: [12000, 14500, 18500, 16000, 21000],
                    backgroundColor: "#6f4e37"
                },
                {
                    label: "Costos",
                    data: [5000, 6200, 7200, 6800, 8500],
                    backgroundColor: "#d8b08c"
                },
                {
                    label: "Ganancia",
                    data: [5000, 6300, 8300, 7200, 9500],
                    backgroundColor: "#198754"
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}


// Gráfica de distribución
const graficaDistribucion = document.getElementById("graficaDistribucion");

if (graficaDistribucion) {
    new Chart(graficaDistribucion, {
        type: "doughnut",
        data: {
            labels: ["Ganancia libre", "Reserva", "Reinversión"],
            datasets: [
                {
                    data: [2800, 3000, 2500],
                    backgroundColor: ["#198754", "#6f4e37", "#d8b08c"]
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}


// Calculadora visual de ganancias
const btnCalcularGanancia = document.getElementById("btnCalcularGanancia");

if (btnCalcularGanancia) {
    btnCalcularGanancia.addEventListener("click", function () {
        const ingresos = Number(document.getElementById("ingresos").value);
        const costos = Number(document.getElementById("costos").value);
        const gastos = Number(document.getElementById("gastos").value);
        const reserva = Number(document.getElementById("reserva").value);
        const reinversion = Number(document.getElementById("reinversion").value);

        const gananciaFinal = ingresos - costos - gastos - reserva - reinversion;

        const resultado = document.querySelector(".profit-box h2");
        resultado.textContent = "RD$ " + gananciaFinal.toFixed(2);

        alert("Ganancia calculada correctamente.");
    });
}