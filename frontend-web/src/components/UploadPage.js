import React from "react";
import { useNavigate } from "react-router-dom";
import FileUpload from "./FileUpload";

const UploadPage = () => {
  const navigate = useNavigate();

  const handleUploadSuccess = (data) => {
    // data should include file_id
    navigate(`/analysis/${data.file_id}`, { state: { stats: data } });
  };

  return (
    <div className="app-container">
      <h2>Upload CSV Data</h2>
      <p style={{ color: "var(--text-secondary)" }}>
        Upload your equipment CSV and view analysis report.
      </p>
      <div className="card">
        <FileUpload onUploadSuccess={handleUploadSuccess} />
      </div>
    </div>
  );
};

export default UploadPage;
