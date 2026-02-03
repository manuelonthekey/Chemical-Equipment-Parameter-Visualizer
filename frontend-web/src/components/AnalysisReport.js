import React, { useEffect, useState } from "react";
import { useLocation, Link, useParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
);

const AnalysisReport = () => {
  const { state } = useLocation();
  const { id } = useParams();
  const [stats, setStats] = useState(state?.stats || null);
  const { token } = useAuth();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/history/${id}/`, {
          headers: { Authorization: `Token ${token}` },
        });
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch analysis", err);
      }
    };

    if (!stats && id) fetchStats();
  }, [id, stats, token]);

  if (!stats) return <div className="app-container"><p>Loading analysis...</p></div>;

  // Prepare bar chart (grouped bars per equipment)
  const labels = stats.records.map((r) => r['Equipment Name']);
  const flowData = stats.records.map((r) => r['Flowrate']);
  const pressureData = stats.records.map((r) => r['Pressure']);
  const tempData = stats.records.map((r) => r['Temperature']);

  const barData = {
    labels,
    datasets: [
      {
        label: "Flowrate",
        data: flowData,
        backgroundColor: "rgba(75, 192, 192, 0.8)",
      },
      {
        label: "Pressure",
        data: pressureData,
        backgroundColor: "rgba(54, 162, 235, 0.8)",
      },
      {
        label: "Temperature",
        data: tempData,
        backgroundColor: "rgba(255, 99, 132, 0.8)",
      },
    ],
  };

  const barOptions = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Equipment Metrics (Grouped)" },
    },
  };

  // Donut chart for type distribution
  const types = Object.keys(stats.type_distribution || {});
  const typeValues = types.map((t) => stats.type_distribution[t]);
  const donutData = {
    labels: types,
    datasets: [
      {
        data: typeValues,
        backgroundColor: [
          "#60a5fa",
          "#34d399",
          "#f59e0b",
          "#f87171",
          "#a78bfa",
        ],
      },
    ],
  };

  return (
    <div className="app-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Analysis Report</h2>
        <div>
          <Link to="/" className="reset-btn" style={{ marginRight: 8 }}>Dashboard</Link>
          <Link to="/history" className="reset-btn">History</Link>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 330px", gap: 20, marginTop: 20 }}>
        <div className="card">
          <h3>Grouped Metrics</h3>
          <div className="chart-container">
            <Bar data={barData} options={barOptions} />
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <h3>Equipment Type Distribution</h3>
            <div style={{ width: "100%", height: 240 }}>
              <Doughnut data={donutData} />
            </div>
          </div>

          <div className="card">
            <h3>Average Parameters</h3>
            <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
              <div className="stat-card card" style={{ flex: 1 }}>
                <div>
                  <svg className="icon" viewBox="0 0 24 24" fill="none"><path d="M3 12h18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span className="label">Flowrate</span>
                </div>
                <span className="value">{stats.averages.flowrate}</span>
              </div>

              <div className="stat-card card" style={{ flex: 1 }}>
                <div>
                  <svg className="icon" viewBox="0 0 24 24" fill="none"><path d="M12 3v18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span className="label">Pressure</span>
                </div>
                <span className="value">{stats.averages.pressure}</span>
              </div>

              <div className="stat-card card" style={{ flex: 1 }}>
                <div>
                  <svg className="icon" viewBox="0 0 24 24" fill="none"><path d="M12 2v8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M8 14h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
                  <span className="label">Temperature</span>
                </div>
                <span className="value">{stats.averages.temperature}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default AnalysisReport;
