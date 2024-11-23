// Fetch data passed from the Chrome extension
const queryParams = new URLSearchParams(window.location.search);
const analyticsData = JSON.parse(queryParams.get("data"));

const { top_safe, top_unsafe } = analyticsData;

// Utility: Truncate labels to avoid overflow
function truncateLabel(label, maxLength = 10) {
  return label.length > maxLength
    ? label.substring(0, maxLength - 1) + "…"
    : label;
}

// Utility: Error handling for empty datasets
function checkEmptyData(data, chartName) {
  if (!data || data.length === 0) {
    console.warn(`No data available for ${chartName}.`);
    return true;
  }
  return false;
}

// Render Safe and Unsafe Graphs
function renderGraph(canvasId, data, color, title) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  if (checkEmptyData(data, title)) return;

  // Prepare data for plotting
  const labels = data.map((item) => truncateLabel(item.feature));
  const values = data.map((item) => Math.abs(item.shap_value));
  const maxValue = Math.max(...values);

  // Calculate dynamic bar width
  const barWidth = Math.max(canvas.width / labels.length - 10, 20);

  // Plot bars
  labels.forEach((label, index) => {
    const value = values[index];
    const barHeight = (value / maxValue) * (canvas.height * 0.8);
    const x = index * (barWidth + 10) + 10;
    const y = canvas.height - barHeight;

    ctx.fillStyle = color;
    ctx.fillRect(x, y, barWidth, barHeight);

    // Add feature labels below each bar
    ctx.fillStyle = "#000";
    ctx.font = "12px Arial";
    ctx.fillText(label, x, canvas.height - 5, barWidth);
  });

  // Draw the axis line
  ctx.strokeStyle = "#000";
  ctx.beginPath();
  ctx.moveTo(0, canvas.height - 1);
  ctx.lineTo(canvas.width, canvas.height - 1);
  ctx.stroke();
}

// Render Safe and Unsafe Contributors
renderGraph("safe-graph", top_safe, "#1E8449", "Safe Contributions");
renderGraph("unsafe-graph", top_unsafe, "#C62828", "Unsafe Contributions");

// Render Cumulative Contribution Pie Chart
function renderPieChart(canvasId, safeData, unsafeData) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  if (checkEmptyData(safeData.concat(unsafeData), "Cumulative Pie Chart"))
    return;

  // Calculate total contributions
  const safeSum = safeData.reduce(
    (sum, item) => sum + Math.abs(item.shap_value),
    0
  );
  const unsafeSum = unsafeData.reduce(
    (sum, item) => sum + Math.abs(item.shap_value),
    0
  );

  new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Safe Contributions", "Unsafe Contributions"],
      datasets: [
        {
          data: [safeSum, unsafeSum],
          backgroundColor: ["#1E8449", "#C62828"], // Green and Red
        },
      ],
    },
    options: {
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });
}

renderPieChart("cumulative-pie", top_safe, top_unsafe);

// Render Feature Importance Horizontal Bar Chart
function renderHorizontalBarChart(canvasId, safeData, unsafeData) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  if (
    checkEmptyData(safeData.concat(unsafeData), "Feature Importance Bar Chart")
  )
    return;

  const allData = [...safeData, ...unsafeData];
  allData.sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));

  const labels = allData.map((item) => truncateLabel(item.feature));
  const values = allData.map((item) => item.shap_value);

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "SHAP Value Contribution",
          data: values,
          backgroundColor: values.map((value) =>
            value > 0 ? "#C62828" : "#1E8449"
          ), // Red for unsafe, Green for safe
        },
      ],
    },
    options: {
      indexAxis: "y",
      plugins: {
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          beginAtZero: true,
        },
      },
    },
  });
}

renderHorizontalBarChart("feature-importance-bar", top_safe, top_unsafe);

// Render Line Graph for Prediction Evolution
function renderLineGraph(canvasId, safeData, unsafeData) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext("2d");

  if (
    checkEmptyData(
      safeData.concat(unsafeData),
      "Prediction Evolution Line Chart"
    )
  )
    return;

  const cumulativeSafe = safeData.map((_, index) =>
    safeData.slice(0, index + 1).reduce((sum, i) => sum + i.shap_value, 0)
  );
  const cumulativeUnsafe = unsafeData.map((_, index) =>
    unsafeData.slice(0, index + 1).reduce((sum, i) => sum + i.shap_value, 0)
  );

  new Chart(ctx, {
    type: "line",
    data: {
      labels: [
        ...safeData.map((item) => truncateLabel(item.feature)),
        ...unsafeData.map((item) => truncateLabel(item.feature)),
      ],
      datasets: [
        {
          label: "Cumulative Safe Contribution",
          data: cumulativeSafe,
          borderColor: "#1E8449", // Green
          fill: false,
          tension: 0.3,
        },
        {
          label: "Cumulative Unsafe Contribution",
          data: cumulativeUnsafe,
          borderColor: "#C62828", // Red
          fill: false,
          tension: 0.3,
        },
      ],
    },
    options: {
      plugins: {
        legend: {
          position: "top",
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: "Feature",
          },
        },
        y: {
          title: {
            display: true,
            text: "Cumulative SHAP Value",
          },
        },
      },
    },
  });
}

renderLineGraph("prediction-evolution-line", top_safe, top_unsafe);

// SAVED
