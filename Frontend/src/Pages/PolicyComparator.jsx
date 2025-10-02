import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import Loading from "../components/Loading";

export default function PolicyComparator() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [method, setMethod] = useState("text"); // text or file
  const navigate = useNavigate();

  const handleCompare = async () => {
    setError("");
    setLoading(true);
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/policy/compare",
        {
          policy1,
          policy2,
        }
      );

      navigate("/result", { state: { result: response.data } });
    } catch (err) {
      setError("❌ " + (err.response?.data?.detail || "Failed to compare policies. Please try again."));
      console.error(err);
    }
    setLoading(false);
  };

  const handleFileUpload = async (files, policyNumber) => {
    if (!files || !files[0]) return;

    const file = files[0];
    if (file.type !== "application/pdf") {
      setError("❌ Please upload PDF files only");
      return;
    }

    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const text = e.target.result;
        if (policyNumber === 1) {
          setPolicy1(text);
        } else {
          setPolicy2(text);
        }
      };
      reader.readAsText(file);
    } catch (err) {
      setError("❌ Error reading file");
      console.error(err);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white shadow-xl rounded-2xl p-8 md:p-10">
        {/* Header */}
        <div className="max-w-3xl mx-auto text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-800 mb-4">
            Climate Policy Comparator
          </h1>
          <p className="text-lg text-gray-600">
            Our AI-powered tool analyzes and compares climate policies, identifying
            key similarities, differences, and climate impact factors.
          </p>
        </div>

        {/* Input Method Toggle */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex rounded-lg border border-gray-200 p-1">
            <button
              onClick={() => setMethod("text")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${method === "text"
                ? "bg-indigo-100 text-indigo-700"
                : "text-gray-500 hover:text-indigo-600"}`}
            >
              ✍️ Paste Text
            </button>
            <button
              onClick={() => setMethod("file")}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${method === "file"
                ? "bg-indigo-100 text-indigo-700"
                : "text-gray-500 hover:text-indigo-600"}`}
            >
              📄 Upload PDF
            </button>
          </div>
        </div>

        {/* Input Section */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Policy A */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
                A
              </div>
              <h3 className="text-lg font-semibold text-gray-800">First Policy</h3>
            </div>
            {method === "text" ? (
              <textarea
                className="w-full h-64 border-2 border-gray-200 rounded-xl p-4 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                value={policy1}
                onChange={(e) => setPolicy1(e.target.value)}
                placeholder="Paste or type the first policy text here..."
              />
            ) : (
              <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileUpload(e.target.files, 1)}
                  className="hidden"
                  id="policy1-upload"
                />
                <label
                  htmlFor="policy1-upload"
                  className="cursor-pointer flex flex-col items-center space-y-2"
                >
                  <div className="w-12 h-12 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center">
                    <svg
                      className="w-6 h-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                      />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-600">
                    Click to upload PDF or drag and drop
                  </span>
                </label>
              </div>
            )}
          </div>

          {/* Policy B */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-bold">
                B
              </div>
              <h3 className="text-lg font-semibold text-gray-800">Second Policy</h3>
            </div>
            {method === "text" ? (
              <textarea
                className="w-full h-64 border-2 border-gray-200 rounded-xl p-4 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                value={policy2}
                onChange={(e) => setPolicy2(e.target.value)}
                placeholder="Paste or type the second policy text here..."
              />
            ) : (
              <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileUpload(e.target.files, 2)}
                  className="hidden"
                  id="policy2-upload"
                />
                <label
                  htmlFor="policy2-upload"
                  className="cursor-pointer flex flex-col items-center space-y-2"
                >
                  <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center">
                    <svg
                      className="w-6 h-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                      />
                    </svg>
                  </div>
                  <span className="text-sm text-gray-600">
                    Click to upload PDF or drag and drop
                  </span>
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Action Section */}
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={handleCompare}
            disabled={!policy1 || !policy2 || loading}
            className={`px-8 py-3 text-white rounded-xl font-medium shadow-lg transition transform hover:scale-105 ${loading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
              } disabled:opacity-50 disabled:transform-none`}
          >
            {loading ? "Analyzing..." : "� Compare Policies"}
          </button>

          {loading && <Loading />}

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-medium">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="mt-16 grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Policy Analysis</h3>
          <p className="text-gray-600">
            Advanced text analysis identifies key policy components and climate factors.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Impact Comparison</h3>
          <p className="text-gray-600">
            Compare environmental impact metrics and effectiveness scores between policies.
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="w-10 h-10 rounded-full bg-yellow-100 text-yellow-600 flex items-center justify-center mb-4">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">AI-Powered Insights</h3>
          <p className="text-gray-600">
            Get intelligent recommendations and insights backed by machine learning.
          </p>
        </div>
      </div>
    </div>
  );
}
