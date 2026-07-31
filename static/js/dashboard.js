// Gráfica de ventas semanales
const graficaVentasDashboard = document.getElementById("graficaVentasDashboard");

if (graficaVentasDashboard) {
    new Chart(graficaVentasDashboard, {
        type: "line",
        data: {
            labels: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
            datasets: [{
                label: "Ventas",
                data: [12000, 14500, 18500, 16000, 21000],
                borderColor: "#6f4e37",
                backgroundColor: "rgba(111, 78, 55, 0.15)",
                fill: true,
                tension: 0.4
            }]
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


// Gráfica de productos más vendidos
const graficaProductosDashboard = document.getElementById("graficaProductosDashboard");

if (graficaProductosDashboard) {
    new Chart(graficaProductosDashboard, {
        type: "doughnut",
        data: {
            labels: ["Café", "Jugos", "Sandwich", "Batidas"],
            datasets: [{
                data: [35, 25, 20, 20],
                backgroundColor: ["#6f4e37", "#d8b08c", "#198754", "#c89f7a"]
            }]
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