import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function PolicyAnalyzer() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError("");
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return setError("Please select a file.");

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/policy/full-analysis",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      navigate("/result", { state: { analysis: response.data } });
    } catch (err) {
      console.error(err);
      setError("Error uploading or processing document.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6 text-center">
          Analyze Your Policy Documents
        </h2>

        <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
          {/* Drag & Drop Zone */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer ${
              dragActive
                ? "border-blue-500 bg-blue-50"
                : file
                ? "border-green-500 bg-green-50"
                : "border-gray-300 hover:border-blue-400 bg-gray-50"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              onChange={handleFileChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              accept=".pdf,.doc,.docx,.txt"
            />
            <div className="flex flex-col items-center gap-4 pointer-events-none">
              {file ? (
                <>
                  <p className="text-lg font-semibold text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                    }}
                    className="text-sm text-red-600 hover:text-red-700 font-medium pointer-events-auto"
                  >
                    Remove file
                  </button>
                </>
              ) : (
                <p className="text-gray-500">Drop your file here or click to browse</p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && <p className="text-red-600 mt-4">{error}</p>}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!file || loading}
            className="mt-6 w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Analyzing Document..." : "Upload & Analyze"}
          </button>
        </form>
      </div>
    </div>
  );
}
