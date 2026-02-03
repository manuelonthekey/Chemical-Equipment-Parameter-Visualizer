import React, { useState } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";

const FileUpload = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fileName, setFileName] = useState("");
  const { token } = useAuth();

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) {
      setFileName("");
      return;
    }
    setFileName(file.name);

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
    <div className="upload-card">
      <input
        id="csv-upload"
        className="file-input"
        type="file"
        onChange={handleUpload}
        accept=".csv"
      />
      <label htmlFor="csv-upload" className="upload-drop">
        <div className="upload-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path
              d="M12 15V7"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M8.5 10.5L12 7l3.5 3.5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M5 15.5a4.5 4.5 0 014.5-4.5h.8"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M19 15.5a4.5 4.5 0 00-4.5-4.5h-.8"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M6 15.5v1A2.5 2.5 0 008.5 19h7a2.5 2.5 0 002.5-2.5v-1"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <p className="upload-drop-title">Drag &amp; Drop your CSV file here</p>
        <p className="upload-drop-sub">or click to browse</p>
      </label>
      {fileName ? <div className="file-name">{fileName}</div> : null}
      {loading && <p className="upload-status">Processing data...</p>}
      {error && <div className="upload-error-banner">{error}</div>}
      <p className="upload-support">
        Supported format: .csv (Equipment Name, Type, Flowrate, Pressure,
        Temperature)
      </p>
    </div>
  );
};

export default FileUpload;
