import React, { useState } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

const FileUpload = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { token } = useAuth();

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError("");

    try {
      if (!token) {
        setError("Please log in to upload files.");
        return;
      }
      // Sending to the Backend API
      const res = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/upload/`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Token ${token}`,
          },
        },
      );
      // Pass data back up to App.js
      onUploadSuccess(res.data);
    } catch (err) {
      console.error(err);
      setError("Failed to upload file. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card upload-section">
      <h3>Upload CSV Data</h3>
      <input type="file" onChange={handleUpload} accept=".csv" />
      {loading && <p style={{ color: "blue" }}>Processing data...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
};

export default FileUpload;
