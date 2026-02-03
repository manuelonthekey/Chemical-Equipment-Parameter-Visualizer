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
  const location = useLocation();
  const localStats = stats || location.state?.stats;
  if (!localStats)
    return (
      <div className="app-container">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2>Dashboard</h2>
          <div>
            <Link to="/upload" className="reset-btn" style={{ marginRight: 8 }}>
              Upload
            </Link>
            <Link to="/history" className="reset-btn">
              History
            </Link>
          </div>
        </div>

        <div className="card" style={{ marginTop: 20 }}>
          <h3>No data loaded</h3>
          <p style={{ color: "var(--text-secondary)" }}>
            Upload a CSV or select an item from{" "}
            <Link to="/history">History</Link> to view an analysis report.
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
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Equipment Average Metrics" },
    },
  };

  return (
    <div className="card">
      <h3>Summary Statistics</h3>
      <p>
        <strong>Total Equipment Count:</strong> {localStats.total_count}
      </p>

      <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
        <div className="stat-card card" style={{ flex: 1 }}>
          <div>
            <svg className="icon" viewBox="0 0 24 24" fill="none">
              <path
                d="M3 12h18"
                stroke="currentColor"
                strokeWidth="1.5"
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
                d="M12 3v18"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="label">Pressure</span>
          </div>
          <span className="value">{localStats.averages.pressure}</span>
        </div>

        <div className="stat-card card" style={{ flex: 1 }}>
          <div>
            <svg className="icon" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2v8"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M8 14h8"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="label">Temperature</span>
          </div>
          <span className="value">{localStats.averages.temperature}</span>
        </div>
      </div>

      <div style={{ marginTop: "20px" }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

export default Dashboard;
