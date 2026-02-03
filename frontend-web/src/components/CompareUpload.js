import React, { useState } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return value.toFixed(2);
  return value;
};

const deltaClass = (value) => {
  if (value === null || value === undefined) return "";
  if (value > 0) return "delta-up";
  if (value < 0) return "delta-down";
  return "delta-zero";
};

const CompareUpload = () => {
  const { token } = useAuth();
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleCompare = async () => {
    if (!fileA || !fileB) {
      setError("Please select both CSV files before comparing.");
      return;
    }
    if (!token) {
      setError("Please log in to compare files.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file_a", fileA);
    formData.append("file_b", fileB);

    try {
      const res = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/compare/`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Token ${token}`,
          },
        },
      );
      setResult(res.data);
    } catch (err) {
      const message =
        err.response?.data?.error ||
        "Failed to compare files. Ensure backend is running.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const diffRows = result?.diff?.rows || [];

  return (
    <div className="compare-section">
      <div className="compare-card">
        <div className="compare-inputs">
          <label className="compare-file">
            <span className="compare-label">CSV A</span>
            <input
              type="file"
              accept=".csv"
              onChange={(event) => setFileA(event.target.files[0] || null)}
            />
            <span className="compare-name">
              {fileA ? fileA.name : "Choose file"}
            </span>
          </label>

          <label className="compare-file">
            <span className="compare-label">CSV B</span>
            <input
              type="file"
              accept=".csv"
              onChange={(event) => setFileB(event.target.files[0] || null)}
            />
            <span className="compare-name">
              {fileB ? fileB.name : "Choose file"}
            </span>
          </label>
        </div>

        <button
          type="button"
          className="reset-btn compare-btn"
          onClick={handleCompare}
          disabled={loading}
        >
          {loading ? "Comparing..." : "Compare CSVs"}
        </button>

        {error && <div className="upload-error-banner">{error}</div>}
      </div>

      {result && (
        <div className="compare-results">
          <div className="compare-summary">
            <div className="compare-panel">
              <h4>File A Summary</h4>
              <p>Total Records: {result.file_a?.total_count}</p>
              <p>Avg Flowrate: {formatValue(result.file_a?.averages?.flowrate)}</p>
              <p>Avg Pressure: {formatValue(result.file_a?.averages?.pressure)}</p>
              <p>
                Avg Temperature:{" "}
                {formatValue(result.file_a?.averages?.temperature)}
              </p>
            </div>

            <div className="compare-panel">
              <h4>File B Summary</h4>
              <p>Total Records: {result.file_b?.total_count}</p>
              <p>Avg Flowrate: {formatValue(result.file_b?.averages?.flowrate)}</p>
              <p>Avg Pressure: {formatValue(result.file_b?.averages?.pressure)}</p>
              <p>
                Avg Temperature:{" "}
                {formatValue(result.file_b?.averages?.temperature)}
              </p>
            </div>

            <div className="compare-panel">
              <h4>Diff Summary</h4>
              <p>Only in A: {result.diff?.summary?.only_in_a}</p>
              <p>Only in B: {result.diff?.summary?.only_in_b}</p>
              <p>In Both: {result.diff?.summary?.in_both}</p>
            </div>
          </div>

          <div className="card compare-table">
            <h3>Per-Equipment Differences</h3>
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Equipment</th>
                    <th>Type A</th>
                    <th>Type B</th>
                    <th>Flow A</th>
                    <th>Flow B</th>
                    <th>Δ Flow</th>
                    <th>Pressure A</th>
                    <th>Pressure B</th>
                    <th>Δ Pressure</th>
                    <th>Temp A</th>
                    <th>Temp B</th>
                    <th>Δ Temp</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {diffRows.length > 0 ? (
                    diffRows.map((row) => (
                      <tr key={row.equipment_name}>
                        <td>{row.equipment_name}</td>
                        <td>{formatValue(row.type_a)}</td>
                        <td>{formatValue(row.type_b)}</td>
                        <td>{formatValue(row.flowrate_a)}</td>
                        <td>{formatValue(row.flowrate_b)}</td>
                        <td className={deltaClass(row.flowrate_delta)}>
                          {formatValue(row.flowrate_delta)}
                        </td>
                        <td>{formatValue(row.pressure_a)}</td>
                        <td>{formatValue(row.pressure_b)}</td>
                        <td className={deltaClass(row.pressure_delta)}>
                          {formatValue(row.pressure_delta)}
                        </td>
                        <td>{formatValue(row.temperature_a)}</td>
                        <td>{formatValue(row.temperature_b)}</td>
                        <td className={deltaClass(row.temperature_delta)}>
                          {formatValue(row.temperature_delta)}
                        </td>
                        <td>{row.status}</td>
                      </tr>
                    ))
                  ) : (
                    <tr className="raw-empty-row">
                      <td colSpan={13}>No comparison data available.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompareUpload;
