function createPieChart() {
    const canvas = document.getElementById("expensePieChart");
    if (!canvas || typeof Chart === "undefined") return;

    if (!expenseLabels.length) {
        canvas.parentElement.insertAdjacentHTML(
            "beforeend",
            '<p class="text-muted mt-3 mb-0">Нет расходов за текущий месяц.</p>'
        );
        return;
    }

    new Chart(canvas, {
        type: "pie",
        data: {
            labels: expenseLabels,
            datasets: [
                {
                    data: expenseValues,
                    backgroundColor: [
                        "#c1121f",
                        "#101010",
                        "#2b2d42",
                        "#6c757d",
                        "#8d99ae",
                        "#ef233c",
                        "#343a40",
                    ],
                },
            ],
        },
    });
}

function createMonthlyBarChart() {
    const canvas = document.getElementById("monthlyBarChart");
    if (!canvas || typeof Chart === "undefined") return;

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: monthLabels,
            datasets: [
                {
                    label: "Доходы",
                    data: incomeValues,
                    backgroundColor: "#101010",
                },
                {
                    label: "Расходы",
                    data: expenseMonthValues,
                    backgroundColor: "#c1121f",
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                },
            },
        },
    });
}

createPieChart();
createMonthlyBarChart();
