const baseChartOptions = {
  responsive: true,
  plugins: {
    legend: {
      display: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
    },
  },
};

const makeLineChart = (ctx, label, data) =>
  new Chart(ctx, {
    type: "line",
    data: {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      datasets: [
        {
          label,
          data,
          borderColor: "#0ea5a4",
          backgroundColor: "rgba(14, 165, 164, 0.2)",
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: baseChartOptions,
  });

const makeBarChart = (ctx, labels, data) =>
  new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Count",
          data,
          backgroundColor: ["#0ea5a4", "#0b2b26", "#8ab4f8", "#f59e0b"],
        },
      ],
    },
    options: baseChartOptions,
  });

document.addEventListener("DOMContentLoaded", () => {
  makeLineChart(document.getElementById("chartCaptures"), "Captures", [12, 19, 8, 15, 22, 18]);
  makeBarChart(
    document.getElementById("chartAdoption"),
    ["Adopted", "Reclaimed"],
    [24, 18],
  );
  makeBarChart(
    document.getElementById("chartBarangay"),
    ["Poblacion", "Banga", "San Isidro", "Villareal"],
    [14, 9, 11, 7],
  );
  makeBarChart(
    document.getElementById("chartRevenue"),
    ["Section 28", "Section 29"],
    [12000, 6400],
  );
});
