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
    primaryStrong: getCssVar("--color-primary-700", "#0f5e3c"),
    accent: getCssVar("--color-accent", "#f6d88b"),
    ink: getCssVar("--color-ink", "#0b2b26"),
    muted: getCssVar("--color-muted", "#5f6f68"),
    surface: getCssVar("--color-surface", "#ffffff"),
  };

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;
  const formatNumber = (value) => new Intl.NumberFormat().format(value);

  const grid = hexToRgba(palette.ink, 0.08);
  const axisBorder = hexToRgba(palette.ink, 0.12);

  const baseChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    animation: prefersReducedMotion
      ? false
      : {
          duration: 900,
          easing: "easeOutQuart",
        },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: palette.ink,
        titleColor: "#ffffff",
        bodyColor: "#ffffff",
        borderColor: axisBorder,
        borderWidth: 1,
        padding: 10,
        displayColors: false,
        callbacks: {
          label: (context) => {
            const label = context.dataset?.label || "Value";
            const value = context.parsed?.y ?? context.parsed;
            return `${label}: ${formatNumber(value ?? 0)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: palette.muted,
          maxRotation: 0,
          autoSkipPadding: 12,
        },
        border: {
          color: axisBorder,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: grid,
          borderDash: [4, 4],
        },
        ticks: {
          color: palette.muted,
          padding: 6,
          callback: (value) => formatNumber(value),
        },
        border: {
          color: axisBorder,
        },
      },
    },
  };

  const setChartFallback = (canvas, hasData) => {
    const panel =
      canvas.closest(".analytics-panel") || canvas.closest(".card-elevated");
    if (!panel) return;
    const fallback = panel.querySelector(".chart-fallback");
    if (!fallback) return;
    fallback.classList.toggle("is-hidden", hasData);
    panel.classList.toggle("is-empty", !hasData);
    canvas.classList.toggle("is-hidden", !hasData);
  };

  const getBarThickness = (labelCount = 0) => {
    const width = window.innerWidth;
    const base = width < 576 ? 22 : width < 992 ? 28 : 34;
    if (labelCount > 10) return Math.max(16, Math.round(base * 0.8));
    if (labelCount > 6) return Math.max(18, Math.round(base * 0.9));
    return base;
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
            borderColor: palette.primaryStrong,
            backgroundColor: (context) => {
              const { chart } = context;
              const { ctx: canvasContext, chartArea } = chart;
              if (!chartArea) {
                return hexToRgba(palette.primary, 0.18);
              }
              const gradient = canvasContext.createLinearGradient(
                0,
                chartArea.top,
                0,
                chartArea.bottom,
              );
              gradient.addColorStop(0, hexToRgba(palette.primary, 0.35));
              gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
              return gradient;
            },
            tension: 0.32,
            borderWidth: 2.5,
            fill: true,
            pointBackgroundColor: palette.surface,
            pointBorderColor: palette.primaryStrong,
            pointBorderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointHoverBorderWidth: 2,
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
  const chartData = chartDataElement
    ? JSON.parse(chartDataElement.textContent)
    : null;

  const capturesData = chartData?.captures ?? { labels: [], data: [] };
  const adoptionData = chartData?.adoption_vs_reclaim ?? {
    labels: [],
    data: [],
  };

  const capturesCanvas = document.getElementById("chartCaptures");
  if (capturesCanvas) {
    const hasCapturesData =
      Array.isArray(capturesData.labels) &&
      capturesData.labels.length > 0 &&
      Array.isArray(capturesData.data) &&
      capturesData.data.length > 0;
    setChartFallback(capturesCanvas, hasCapturesData);
    if (hasCapturesData) {
      makeLineChart(
        capturesCanvas,
        "Captures",
        capturesData.labels,
        capturesData.data,
      );
    }
  }

  const adoptionCanvas = document.getElementById("chartAdoption");
  if (adoptionCanvas) {
    const adoptionLabels = Array.isArray(adoptionData.labels)
      ? adoptionData.labels
      : [];
    let datasets = [];
    let showLegend = false;
    let hasAdoptionData = false;

    if (Array.isArray(adoptionData.datasets) && adoptionData.datasets.length > 0) {
      hasAdoptionData = adoptionData.datasets.some(
        (dataset) => Array.isArray(dataset.data) && dataset.data.length > 0,
      );
      datasets = adoptionData.datasets.map((dataset, index) => {
        const color = index === 0 ? palette.primary : palette.accent;
        return {
          label: dataset.label,
          data: dataset.data,
          backgroundColor: color,
          hoverBackgroundColor: hexToRgba(color, 0.85),
          borderColor: axisBorder,
          borderWidth: 1,
          borderRadius: 10,
          maxBarThickness: getBarThickness(adoptionLabels.length),
          barPercentage: 0.7,
          categoryPercentage: 0.7,
        };
      });
      showLegend = true;
    } else if (Array.isArray(adoptionData.data)) {
      hasAdoptionData = adoptionData.data.length > 0;
      datasets = [
        {
          label: "Count",
          data: adoptionData.data,
          backgroundColor: [palette.primary, palette.accent],
          hoverBackgroundColor: [
            hexToRgba(palette.primary, 0.85),
            hexToRgba(palette.accent, 0.85),
          ],
          borderColor: axisBorder,
          borderWidth: 1,
          borderRadius: 10,
          maxBarThickness: getBarThickness(adoptionLabels.length),
          barPercentage: 0.7,
          categoryPercentage: 0.7,
        },
      ];
    }

    const hasLabels = adoptionLabels.length > 0;
    const shouldRender = hasLabels && hasAdoptionData;
    setChartFallback(adoptionCanvas, shouldRender);

    if (shouldRender) {
      makeBarChart(adoptionCanvas, adoptionLabels, datasets, {
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
  }
});
