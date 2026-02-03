import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const loadFavorites = () => {
  try {
    const raw = localStorage.getItem("historyFavorites");
    if (!raw) return {};
    const ids = JSON.parse(raw);
    if (!Array.isArray(ids)) return {};
    return ids.reduce((acc, id) => {
      acc[id] = true;
      return acc;
    }, {});
  } catch {
    return {};
  }
};

const History = () => {
  const [history, setHistory] = useState([]);
  const [favorites, setFavorites] = useState(() => loadFavorites());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const { token } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(
          `${process.env.REACT_APP_API_URL}/api/history/`,
          {
            headers: {
              Authorization: `Token ${token}`,
            },
          },
        );
        setHistory(res.data);
      } catch (err) {
        console.error(err);
      }
    };

    if (token) {
      fetchHistory();
    }
  }, [token]);

  useEffect(() => {
    const ids = Object.keys(favorites)
      .filter((key) => favorites[key])
      .map((key) => Number(key))
      .filter((id) => !Number.isNaN(id));
    localStorage.setItem("historyFavorites", JSON.stringify(ids));
  }, [favorites]);

  const handleView = async (id) => {
    try {
      const res = await axios.get(
        `${process.env.REACT_APP_API_URL}/api/history/${id}/`,
        {
          headers: { Authorization: `Token ${token}` },
        },
      );
      navigate(`/analysis/${id}`, { state: { stats: res.data } });
    } catch (err) {
      console.error("Failed to load history item", err);
    }
  };

  const toggleFavorite = (id) => {
    setFavorites((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const filteredHistory = useMemo(() => {
    if (!showFavoritesOnly) return history;
    return history.filter((item) => favorites[item.id]);
  }, [history, favorites, showFavoritesOnly]);

  const favoritesCount = useMemo(
    () => history.filter((item) => favorites[item.id]).length,
    [history, favorites],
  );

  return (
    <div className="app-container">
      <h2>Upload History</h2>
      <p style={{ color: "var(--text-secondary)" }}>
        Click on a row to view the report.
      </p>
      <div className="history-controls">
        <button
          type="button"
          className={`favorite-toggle ${
            showFavoritesOnly ? "is-active" : ""
          }`}
          onClick={() => setShowFavoritesOnly((prev) => !prev)}
        >
          {showFavoritesOnly ? "Showing Favorites" : "Show Favorites"}
        </button>
        <span className="history-count">
          Favorites: {favoritesCount}
        </span>
      </div>
      <div className="history-list card">
        {filteredHistory.length === 0 ? (
          <p style={{ padding: "20px" }}>No uploads yet.</p>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>Favorite</th>
                <th>ID</th>
                <th>File Name</th>
                <th>Uploaded At</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => handleView(item.id)}
                  style={{ cursor: "pointer" }}
                  className="history-row"
                >
                  <td>
                    <button
                      type="button"
                      className={`favorite-btn ${
                        favorites[item.id] ? "is-active" : ""
                      }`}
                      onClick={(event) => {
                        event.stopPropagation();
                        toggleFavorite(item.id);
                      }}
                      aria-label={
                        favorites[item.id]
                          ? "Remove from favorites"
                          : "Add to favorites"
                      }
                    >
                      {favorites[item.id] ? "★" : "☆"}
                    </button>
                  </td>
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
