import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import FileUpload from "./FileUpload";
import CompareUpload from "./CompareUpload";

const UploadPage = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState("single");

  const handleUploadSuccess = (data) => {
    // data should include file_id
    navigate(`/analysis/${data.file_id}`, { state: { stats: data } });
  };

  return (
    <div className="app-container upload-page">
      <div className="upload-switch">
        <button
          type="button"
          className={`switch-btn ${mode === "single" ? "is-active" : ""}`}
          onClick={() => setMode("single")}
        >
          Single Upload
        </button>
        <button
          type="button"
          className={`switch-btn ${mode === "compare" ? "is-active" : ""}`}
          onClick={() => setMode("compare")}
        >
          Compare Two CSVs
        </button>
      </div>

      {mode === "single" ? (
        <FileUpload onUploadSuccess={handleUploadSuccess} />
      ) : (
        <CompareUpload />
      )}
    </div>
  );
};

export default UploadPage;
