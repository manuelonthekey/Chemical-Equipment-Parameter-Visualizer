import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const History = () => {
  const [history, setHistory] = useState([]);
  const { token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get("http://localhost:8000/api/history/", {
          headers: {
            Authorization: `Token ${token}`,
          },
        });
        setHistory(res.data);
      } catch (err) {
        console.error(err);
      }
    };

    if (token) {
      fetchHistory();
    }
  }, [token]);

  const handleView = async (id) => {
    try {
      const res = await axios.get(`http://localhost:8000/api/history/${id}/`, {
        headers: { Authorization: `Token ${token}` },
      });
      navigate("/", { state: { historyData: res.data } });
    } catch (err) {
      console.error("Failed to load history item", err);
    }
  };

  return (
    <div className="app-container">
      <h2>Upload History</h2>
      <p style={{ color: "var(--text-secondary)" }}>
        Click on a row to view the report.
      </p>
      <div className="history-list card">
        {history.length === 0 ? (
          <p style={{ padding: "20px" }}>No uploads yet.</p>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>File Name</th>
                <th>Uploaded At</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => handleView(item.id)}
                  style={{ cursor: "pointer" }}
                  className="history-row"
                >
                  <td>{item.id}</td>
                  <td>{item.file.split("/").pop()}</td>
                  <td>{new Date(item.uploaded_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default History;
