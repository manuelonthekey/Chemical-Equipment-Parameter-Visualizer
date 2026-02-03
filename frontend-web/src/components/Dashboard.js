import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { useTheme } from "../context/ThemeContext";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

const Dashboard = ({ stats }) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const gridColor = isDark
    ? "rgba(237, 233, 254, 0.14)"
    : "rgba(30, 41, 59, 0.12)";
  const tickColor = isDark
    ? "rgba(237, 233, 254, 0.75)"
    : "rgba(30, 41, 59, 0.7)";
  const axisBorder = isDark
    ? "rgba(237, 233, 254, 0.2)"
    : "rgba(30, 41, 59, 0.2)";
  const location = useLocation();
  const localStats = stats || location.state?.stats;
  if (!localStats)
    return (
      <div className="app-container">
        <div className="dashboard-header">
          <h2>Dashboard</h2>
        </div>

        <div className="card" style={{ marginTop: 20 }}>
          <h3>No data loaded</h3>
          <p style={{ color: "var(--text-secondary)" }}>
            <Link to="/upload" className="text-link">
              Upload
            </Link>{" "}
            a CSV or select an item from{" "}
            <Link to="/history" className="text-link">
              History
            </Link>{" "}
            to view an analysis report.
          </p>
        </div>
      </div>
    );

  // Prepare Chart Data
  const chartData = {
    labels: ["Flowrate", "Pressure", "Temperature"],
    datasets: [
      {
        label: "Average Values",
        data: [
          localStats.averages.flowrate,
          localStats.averages.pressure,
          localStats.averages.temperature,
        ],
        backgroundColor: [
          "rgba(75, 192, 192, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 99, 132, 0.6)",
        ],
        borderColor: [
          "rgba(75, 192, 192, 1)",
          "rgba(54, 162, 235, 1)",
          "rgba(255, 99, 132, 1)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Equipment Average Metrics" },
    },
    scales: {
      x: {
        grid: { color: gridColor },
        ticks: { color: tickColor },
        border: { color: axisBorder },
      },
      y: {
        grid: { color: gridColor },
        ticks: { color: tickColor },
        border: { color: axisBorder },
      },
    },
  };

  return (
    <div className="card">
      <h3>Summary Statistics</h3>
      <p>
        <strong>Total Equipment Count:</strong> {localStats.total_count}
      </p>

      <div className="stat-row">
        <div className="stat-card card" style={{ flex: 1 }}>
          <div>
            <svg className="icon" viewBox="0 0 24 24" fill="none">
              <path
                d="M4 12h10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M12 7l4 5-4 5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M4 7c1.4 0 1.4 2 2.8 2s1.4-2 2.8-2"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="label">Flowrate</span>
          </div>
          <span className="value">{localStats.averages.flowrate}</span>
        </div>

        <div className="stat-card card" style={{ flex: 1 }}>
          <div>
            <svg className="icon" viewBox="0 0 24 24" fill="none">
              <path
                d="M4 13a8 8 0 0116 0"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M12 13l3-3"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M7 13h10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="12" cy="13" r="1.2" fill="currentColor" />
            </svg>
            <span className="label">Pressure</span>
          </div>
          <span className="value">{localStats.averages.pressure}</span>
        </div>

        <div className="stat-card card" style={{ flex: 1 }}>
          <div>
            <svg className="icon" viewBox="0 0 24 24" fill="none">
              <path
                d="M10 4a2 2 0 114 0v8a4 4 0 11-4 0V4z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M10 12h4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="12" cy="18" r="1.6" fill="currentColor" />
            </svg>
            <span className="label">Temperature</span>
          </div>
          <span className="value">{localStats.averages.temperature}</span>
        </div>
      </div>

      <div className="chart-container chart-container-sm" style={{ marginTop: 20 }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

export default Dashboard;
