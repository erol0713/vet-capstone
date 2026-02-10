const getCssVar = (name, fallback) => {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
};

const hexToRgba = (hex, alpha) => {
  const raw = hex.replace("#", "");
  if (raw.length !== 6) return hex;
  const r = parseInt(raw.substring(0, 2), 16);
  const g = parseInt(raw.substring(2, 4), 16);
  const b = parseInt(raw.substring(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

document.addEventListener("DOMContentLoaded", () => {
  const palette = {
    primary: getCssVar("--color-primary", "#1f8a5b"),
    warm: getCssVar("--color-warm", "#f6d88b"),
    ink: getCssVar("--color-ink", "#0b2b26"),
    muted: getCssVar("--color-muted", "#5f6f68"),
  };

  const grid = hexToRgba(palette.ink, 0.08);

  const baseChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: palette.ink,
        titleColor: "#ffffff",
        bodyColor: "#ffffff",
        padding: 10,
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: palette.muted,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: grid,
        },
        ticks: {
          color: palette.muted,
        },
      },
    },
  };

  const makeLineChart = (ctx, label, labels, data) =>
    new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label,
            data,
            borderColor: palette.primary,
            backgroundColor: hexToRgba(palette.primary, 0.18),
            tension: 0.3,
            fill: true,
            pointBackgroundColor: "#ffffff",
            pointBorderColor: palette.primary,
            pointBorderWidth: 2,
            pointRadius: 4,
          },
        ],
      },
      options: baseChartOptions,
    });

  const makeBarChart = (ctx, labels, datasets, optionsOverride = {}) =>
    new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets,
      },
      options: {
        ...baseChartOptions,
        ...optionsOverride,
        plugins: {
          ...baseChartOptions.plugins,
          ...(optionsOverride.plugins || {}),
        },
        scales: {
          ...baseChartOptions.scales,
          ...(optionsOverride.scales || {}),
        },
      },
    });

  if (window.Chart) {
    Chart.defaults.font.family = getCssVar(
      "--font-sans",
      "'Source Sans 3', 'Segoe UI', sans-serif",
    );
    Chart.defaults.color = palette.muted;
  }

  const chartDataElement = document.getElementById("analytics-chart-data");
  const chartData = chartDataElement ? JSON.parse(chartDataElement.textContent) : null;

  const capturesData = chartData?.captures ?? { labels: [], data: [] };
  const adoptionData = chartData?.adoption_vs_reclaim ?? {
    labels: [],
    data: [],
  };

  const capturesCanvas = document.getElementById("chartCaptures");
  if (capturesCanvas) {
    makeLineChart(
      capturesCanvas,
      "Captures",
      capturesData.labels,
      capturesData.data,
    );
  }

  const adoptionCanvas = document.getElementById("chartAdoption");
  if (adoptionCanvas) {
    let datasets = [];
    let showLegend = false;

    if (Array.isArray(adoptionData.datasets) && adoptionData.datasets.length > 0) {
      datasets = adoptionData.datasets.map((dataset, index) => ({
        label: dataset.label,
        data: dataset.data,
        backgroundColor: index === 0 ? palette.primary : palette.warm,
        borderRadius: 8,
        maxBarThickness: 32,
      }));
      showLegend = true;
    } else if (Array.isArray(adoptionData.data)) {
      datasets = [
        {
          label: "Count",
          data: adoptionData.data,
          backgroundColor: [palette.primary, palette.warm],
          borderRadius: 8,
          maxBarThickness: 48,
        },
      ];
    }

    makeBarChart(adoptionCanvas, adoptionData.labels, datasets, {
      plugins: {
        legend: {
          display: showLegend,
          position: "bottom",
          labels: {
            usePointStyle: true,
            pointStyle: "circle",
          },
        },
      },
    });
  }
});
