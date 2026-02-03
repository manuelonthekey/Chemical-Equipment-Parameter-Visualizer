import React, { useState, useRef, useEffect, useMemo } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import { useAuth } from "../context/AuthContext";
import { useLocation } from "react-router-dom";
import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
);

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const { token } = useAuth();
  const location = useLocation();
  const [selectedType, setSelectedType] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [flowMin, setFlowMin] = useState("");
  const [flowMax, setFlowMax] = useState("");
  const [pressMin, setPressMin] = useState("");
  const [pressMax, setPressMax] = useState("");
  const [tempMin, setTempMin] = useState("");
  const [tempMax, setTempMax] = useState("");

  useEffect(() => {
    if (location.state?.historyData) {
      setStats(location.state.historyData);
    }
  }, [location]);

  const processFile = async (file) => {
    if (!file) return;

    // Reset states
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setStats(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      if (!token) {
        setError("Please log in to upload files.");
        setIsUploading(false);
        return;
      }
      const res = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/upload/`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Token ${token}`,
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total,
            );
            setUploadProgress(percentCompleted);
          },
        },
      );

      // Artificial delay to show 100% completion briefly
      setTimeout(() => {
        setStats(res.data);
        setIsUploading(false);
      }, 500);
    } catch (err) {
      console.error(err);
      setError("Failed to process file. Please ensure it's a valid CSV.");
      setIsUploading(false);
    }
  };

  const types = useMemo(() => {
    if (!stats?.records) return [];
    const set = new Set(stats.records.map((r) => r["Type"]));
    return ["All", ...Array.from(set)];
  }, [stats]);

  const filteredRecords = useMemo(() => {
    if (!stats?.records) return [];
    return stats.records.filter((r) => {
      const nameOk =
        !searchTerm ||
        String(r["Equipment Name"])
          .toLowerCase()
          .includes(searchTerm.toLowerCase());
      const typeOk = selectedType === "All" || r["Type"] === selectedType;
      const f = parseFloat(r["Flowrate"]);
      const p = parseFloat(r["Pressure"]);
      const t = parseFloat(r["Temperature"]);
      const flowOk =
        (flowMin === "" || f >= parseFloat(flowMin)) &&
        (flowMax === "" || f <= parseFloat(flowMax));
      const pressOk =
        (pressMin === "" || p >= parseFloat(pressMin)) &&
        (pressMax === "" || p <= parseFloat(pressMax));
      const tempOk =
        (tempMin === "" || t >= parseFloat(tempMin)) &&
        (tempMax === "" || t <= parseFloat(tempMax));
      return nameOk && typeOk && flowOk && pressOk && tempOk;
    });
  }, [
    stats,
    selectedType,
    searchTerm,
    flowMin,
    flowMax,
    pressMin,
    pressMax,
    tempMin,
    tempMax,
  ]);

  const names = filteredRecords.map((r) => r["Equipment Name"]);
  const flowSeries = filteredRecords.map((r) => r["Flowrate"]);
  const pressSeries = filteredRecords.map((r) => r["Pressure"]);
  const tempSeries = filteredRecords.map((r) => r["Temperature"]);

  const handleDownloadPDF = async () => {
    const element = document.querySelector(".dashboard");
    if (!element) return;

    try {
      const prevMode = document.body.getAttribute("data-mode");
      document.body.setAttribute("data-mode", "pdf");
      const canvas = await html2canvas(element, { scale: 2 });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      const imgProps = pdf.getImageProperties(imgData);
      const imgHeight = (imgProps.height * pdfWidth) / imgProps.width;

      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, "PNG", 0, position, pdfWidth, imgHeight);
      heightLeft -= pdfHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, pdfWidth, imgHeight);
        heightLeft -= pdfHeight;
      }

      pdf.save(`report_${stats.file_id}.pdf`);
      if (prevMode) document.body.setAttribute("data-mode", prevMode);
      else document.body.removeAttribute("data-mode");
    } catch (err) {
      console.error("PDF Generation failed", err);
      document.body.removeAttribute("data-mode");
    }
  };

  const handleFileSelect = (event) => {
    processFile(event.target.files[0]);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleReset = () => {
    setStats(null);
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
      },
      title: {
        display: true,
        text: "Per-Equipment",
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: "rgba(0, 0, 0, 0.05)",
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>EquipZense</h1>
        <p className="subtitle">Analyze. Visualize. Optimize.</p>
      </header>

      <main className="app-content">
        {!stats ? (
          <div className="upload-container">
            <div
              className={`drop-zone ${isDragging ? "dragging" : ""} ${error ? "error" : ""}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current.click()}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileSelect}
                accept=".csv"
                style={{ display: "none" }}
              />

              <div className="upload-icon">
                <svg
                  width="50"
                  height="50"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M12 16L12 8"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M9 11L12 8 15 11"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M8 16H16"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M3 15C3 17.8284 3 19.2426 3.87868 20.1213C4.75736 21 6.17157 21 9 21H15C17.8284 21 19.2426 21 20.1213 20.1213C21 19.2426 21 17.8284 21 15"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M16 3H8C5.17157 3 3.75736 3 2.87868 3.87868C2 4.75736 2 6.17157 2 9V15"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M22 15V9C22 6.17157 22 4.75736 21.1213 3.87868C20.2426 3 18.8284 3 16 3"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>

              <h3>Drag & Drop your CSV file here</h3>
              <p>or click to browse</p>

              {isUploading && (
                <div className="progress-container">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <span className="progress-text">{uploadProgress}%</span>
                </div>
              )}

              {error && <div className="error-message">{error}</div>}
            </div>

            <div className="sample-info">
              <small>
                Supported format: .csv (Equipment Name, Type, Flowrate,
                Pressure, Temperature)
              </small>
            </div>
          </div>
        ) : (
          <div className="dashboard fade-in">
            <div className="dashboard-header">
              <div>
                <h2>Analysis Results</h2>
                <small style={{ color: "var(--text-secondary)" }}>
                  Uploaded: {new Date(stats.uploaded_at).toLocaleString()}
                </small>
              </div>
              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  className="reset-btn"
                  onClick={handleDownloadPDF}
                  style={{ backgroundColor: "var(--success-color)" }}
                >
                  Download Report
                </button>
                <button className="reset-btn" onClick={handleReset}>
                  Upload New File
                </button>
              </div>
            </div>

            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <div>
                  <label>Type</label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    style={{ marginLeft: 8 }}
                  >
                    {types.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label>Search</label>
                  <input
                    type="text"
                    placeholder="Equipment Name"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={{ marginLeft: 8 }}
                  />
                </div>
                <div>
                  <label>Flowrate</label>
                  <input
                    type="number"
                    value={flowMin}
                    onChange={(e) => setFlowMin(e.target.value)}
                    placeholder="min"
                    style={{ marginLeft: 8, width: 90 }}
                  />
                  <input
                    type="number"
                    value={flowMax}
                    onChange={(e) => setFlowMax(e.target.value)}
                    placeholder="max"
                    style={{ marginLeft: 8, width: 90 }}
                  />
                </div>
                <div>
                  <label>Pressure</label>
                  <input
                    type="number"
                    value={pressMin}
                    onChange={(e) => setPressMin(e.target.value)}
                    placeholder="min"
                    style={{ marginLeft: 8, width: 90 }}
                  />
                  <input
                    type="number"
                    value={pressMax}
                    onChange={(e) => setPressMax(e.target.value)}
                    placeholder="max"
                    style={{ marginLeft: 8, width: 90 }}
                  />
                </div>
                <div>
                  <label>Temperature</label>
                  <input
                    type="number"
                    value={tempMin}
                    onChange={(e) => setTempMin(e.target.value)}
                    placeholder="min"
                    style={{ marginLeft: 8, width: 90 }}
                  />
                  <input
                    type="number"
                    value={tempMax}
                    onChange={(e) => setTempMax(e.target.value)}
                    placeholder="max"
                    style={{ marginLeft: 8, width: 90 }}
                  />
                </div>
              </div>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <h4>Total Records</h4>
                <div className="stat-value">{stats.total_count}</div>
              </div>
              <div className="stat-card">
                <h4>Equipment Types</h4>
                <div className="stat-value">
                  {Object.keys(stats.type_distribution).length}
                </div>
              </div>

              {/* Detailed Averages Display */}
              <div className="stat-card" style={{ gridColumn: "span 2" }}>
                <h4>Average Parameters</h4>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-around",
                    marginTop: "10px",
                  }}
                >
                  <div
                    style={{
                      color: "rgba(75, 192, 192, 1)",
                      fontWeight: "bold",
                    }}
                  >
                    Flowrate: {stats.averages.flowrate}
                  </div>
                  <div
                    style={{
                      color: "rgba(54, 162, 235, 1)",
                      fontWeight: "bold",
                    }}
                  >
                    Pressure: {stats.averages.pressure}
                  </div>
                  <div
                    style={{
                      color: "rgba(255, 99, 132, 1)",
                      fontWeight: "bold",
                    }}
                  >
                    Temperature: {stats.averages.temperature}
                  </div>
                </div>
              </div>
            </div>

            <div className="stats-grid">
              <div className="chart-container card">
                <Line
                  data={{
                    labels: names,
                    datasets: [
                      {
                        label: "Flowrate",
                        data: flowSeries,
                        borderColor: "rgba(75, 192, 192, 1)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        tension: 0.3,
                        pointRadius: 3,
                      },
                    ],
                  }}
                  options={chartOptions}
                />
              </div>
              <div className="chart-container card">
                <Line
                  data={{
                    labels: names,
                    datasets: [
                      {
                        label: "Pressure",
                        data: pressSeries,
                        borderColor: "rgba(54, 162, 235, 1)",
                        backgroundColor: "rgba(54, 162, 235, 0.2)",
                        tension: 0.3,
                        pointRadius: 3,
                      },
                    ],
                  }}
                  options={chartOptions}
                />
              </div>
              <div className="chart-container card">
                <Line
                  data={{
                    labels: names,
                    datasets: [
                      {
                        label: "Temperature",
                        data: tempSeries,
                        borderColor: "rgba(255, 99, 132, 1)",
                        backgroundColor: "rgba(255, 99, 132, 0.2)",
                        tension: 0.3,
                        pointRadius: 3,
                      },
                    ],
                  }}
                  options={chartOptions}
                />
              </div>
            </div>

            <div className="preview-container card">
              <h3>Data Preview</h3>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      {stats.records &&
                        Object.keys(stats.records[0]).map((key) => (
                          <th key={key}>{key}</th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.slice(0, 50).map((row, idx) => (
                      <tr key={idx}>
                        {Object.values(row).map((val, i) => (
                          <td key={i}>{val}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
