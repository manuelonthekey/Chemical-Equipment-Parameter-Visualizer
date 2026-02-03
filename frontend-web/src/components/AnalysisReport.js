import React, { useEffect, useMemo, useState } from "react";
import { useLocation, Link, useParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
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
  const columns = useMemo(
    () => [
      { key: "Equipment Name", label: "Equipment Name" },
      { key: "Type", label: "Type" },
      { key: "Flowrate", label: "Flowrate" },
      { key: "Pressure", label: "Pressure" },
      { key: "Temperature", label: "Temperature" },
    ],
    [],
  );
  const [visibleColumns, setVisibleColumns] = useState(() =>
    Object.fromEntries(
      ["Equipment Name", "Type", "Flowrate", "Pressure", "Temperature"].map(
        (key) => [key, true],
      ),
    ),
  );
  const allTypes = useMemo(() => {
    const list = (stats?.records || [])
      .map((r) => r["Type"])
      .filter(Boolean);
    return Array.from(new Set(list)).sort();
  }, [stats]);
  const [activeTypes, setActiveTypes] = useState([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(
          `${process.env.REACT_APP_API_URL}/api/history/${id}/`,
          {
            headers: { Authorization: `Token ${token}` },
          },
        );
        setStats(res.data);
      } catch (err) {
        console.error("Failed to fetch analysis", err);
      }
    };

    if (!stats && id) fetchStats();
  }, [id, stats, token]);
  const handleDownloadPdf = async () => {
    const reportId = id || stats?.file_id;
    if (!reportId) return;
    setIsDownloading(true);
    setDownloadError("");
    try {
      const res = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/history/${reportId}/report/`,
        {
          headers: { Authorization: `Token ${token}` },
          responseType: "blob",
        },
      );
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `analysis_report_${reportId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError("Failed to download PDF report.");
    } finally {
      setIsDownloading(false);
    }
  };
  useEffect(() => {
    if (allTypes.length) {
      setActiveTypes(allTypes);
    }
  }, [allTypes]);

  if (!stats)
    return (
      <div className="app-container">
        <p>Loading analysis...</p>
      </div>
    );

  // Prepare bar chart (grouped bars per equipment)
  const labels = stats.records.map((r) => r["Equipment Name"]);
  const flowData = stats.records.map((r) => r["Flowrate"]);
  const pressureData = stats.records.map((r) => r["Pressure"]);
  const tempData = stats.records.map((r) => r["Temperature"]);

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
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Equipment Metrics (Grouped)" },
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

  // Donut chart for type distribution
  const types = Object.keys(stats.type_distribution || {});
  const typeValues = types.map((t) => stats.type_distribution[t]);
  const donutColors = [
    "#60a5fa",
    "#34d399",
    "#f59e0b",
    "#f87171",
    "#a78bfa",
    "#4dd0e1",
  ];
  const donutData = {
    labels: types,
    datasets: [
      {
        data: typeValues,
        backgroundColor: donutColors,
      },
    ],
  };
  const donutOptions = {
    plugins: {
      legend: { display: false },
    },
  };
  const toggleColumn = (key) => {
    setVisibleColumns((prev) => {
      const visibleCount = Object.values(prev).filter(Boolean).length;
      if (prev[key] && visibleCount === 1) {
        return prev;
      }
      return { ...prev, [key]: !prev[key] };
    });
  };
  const toggleType = (type) => {
    setActiveTypes((prev) =>
      prev.includes(type)
        ? prev.filter((item) => item !== type)
        : [...prev, type],
    );
  };
  const toggleAllTypes = () => {
    setActiveTypes((prev) =>
      prev.length === allTypes.length ? [] : allTypes,
    );
  };
  const visibleColumnList = columns.filter((col) => visibleColumns[col.key]);
  const rawRows = stats.preview || [];
  const filteredRows =
    activeTypes.length === 0
      ? []
      : rawRows.filter((row) => activeTypes.includes(row["Type"]));

  return (
    <div className="app-container">
      <div className="dashboard-header">
        <h2>Analysis Report</h2>
        <div>
          <button
            type="button"
            className="reset-btn"
            onClick={handleDownloadPdf}
            disabled={isDownloading}
            style={{ marginRight: 8 }}
          >
            {isDownloading ? "Downloading..." : "Download PDF"}
          </button>
          <Link to="/history" className="reset-btn history-btn">
            History
          </Link>
        </div>
      </div>
      {downloadError && (
        <div className="upload-error-banner" style={{ marginBottom: 16 }}>
          {downloadError}
        </div>
      )}

      <div className="analysis-grid">
        <div className="card">
          <h3>Grouped Metrics</h3>
          <div className="chart-container">
            <Bar data={barData} options={barOptions} />
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <h3>Equipment Type Distribution</h3>
            {types.length > 0 && (
              <div className="type-legend">
                {types.map((type, index) => (
                  <div className="type-legend-item" key={type}>
                    <span
                      className="type-legend-swatch"
                      style={{
                        "--legend-color":
                          donutColors[index % donutColors.length],
                      }}
                    />
                    <span className="type-legend-label">{type}</span>
                  </div>
                ))}
              </div>
            )}
            <div style={{ width: "100%", height: 240 }}>
              <Doughnut data={donutData} options={donutOptions} />
            </div>
          </div>

          <div className="card">
            <h3>Average Parameters</h3>
            <div className="avg-cards">
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
                <span className="value">{stats.averages.flowrate}</span>
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
                <span className="value">{stats.averages.pressure}</span>
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
                <span className="value">{stats.averages.temperature}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h3>Sample Records</h3>
        <p className="raw-subtitle">
          Raw data visualizer — toggle columns and filter by equipment type.
        </p>
        <div className="raw-controls">
            <div className="raw-group">
              <div className="raw-group-title">Columns</div>
              <div className="raw-options">
              {columns.map((col) => (
                <label
                  className={`raw-option ${
                    visibleColumns[col.key] ? "is-active" : ""
                  }`}
                  key={col.key}
                >
                  <input
                    type="checkbox"
                    checked={visibleColumns[col.key]}
                    onChange={() => toggleColumn(col.key)}
                  />
                  <span className="raw-check" aria-hidden="true" />
                  <span>{col.label}</span>
                </label>
              ))}
              </div>
            </div>
            <div className="raw-group">
              <div className="raw-group-title">Equipment Types</div>
              <div className="raw-options">
              <button
                className="raw-toggle"
                type="button"
                onClick={toggleAllTypes}
              >
                {activeTypes.length === allTypes.length
                  ? "Clear"
                  : "Select All"}
              </button>
              {allTypes.map((type) => (
                <label
                  className={`raw-option ${
                    activeTypes.includes(type) ? "is-active" : ""
                  }`}
                  key={type}
                >
                  <input
                    type="checkbox"
                    checked={activeTypes.includes(type)}
                    onChange={() => toggleType(type)}
                  />
                  <span className="raw-check" aria-hidden="true" />
                  <span>{type}</span>
                </label>
              ))}
              {allTypes.length === 0 && (
                <span className="raw-empty">No types available.</span>
              )}
            </div>
          </div>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                {visibleColumnList.map((col) => (
                  <th key={col.key}>{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredRows.length > 0 ? (
                filteredRows.map((r, idx) => (
                  <tr key={idx}>
                    {visibleColumnList.map((col) => (
                      <td key={col.key}>{r[col.key]}</td>
                    ))}
                  </tr>
                ))
              ) : (
                <tr className="raw-empty-row">
                  <td colSpan={visibleColumnList.length}>
                    No records match the selected equipment types.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalysisReport;
