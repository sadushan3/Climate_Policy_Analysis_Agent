import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function PolicyComparator() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleCompare = async () => {
    setError("");
    setLoading(true);
    try {
      const response = await axios.post("http://127.0.0.1:8000/api/compare_policy", {
        policy1,
        policy2,
      });

      // ✅ Navigate to /result with backend response
      navigate("/result", { state: { result: response.data } });
    } catch (err) {
      setError("❌ Failed to compare policies. Please try again.");
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white shadow-lg rounded-2xl p-10 max-w-5xl w-full">
        <h1 className="text-4xl font-extrabold text-center text-gray-800 mb-3">
          Instant Policy Comparison
        </h1>
        <p className="text-center text-gray-500 mb-10">
          Paste your policy documents below. Our AI will analyze them and provide
          a clear, side-by-side comparison in seconds.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* Policy A */}
          <div className="border border-gray-200 rounded-xl p-6">
            <label className="block text-gray-700 font-semibold mb-2">
              Policy A
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-400"
              rows="6"
              value={policy1}
              onChange={(e) => setPolicy1(e.target.value)}
              placeholder="Paste the full text of the first policy here."
            />
          </div>

          {/* Policy B */}
          <div className="border border-gray-200 rounded-xl p-6">
            <label className="block text-gray-700 font-semibold mb-2">
              Policy B
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-indigo-400"
              rows="6"
              value={policy2}
              onChange={(e) => setPolicy2(e.target.value)}
              placeholder="Paste the full text of the second policy here."
            />
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={handleCompare}
            disabled={!policy1 || !policy2 || loading}
            className="px-8 py-3 bg-indigo-600 text-white rounded-lg font-medium shadow hover:bg-indigo-700 transition disabled:opacity-50"
          >
            {loading ? "Comparing..." : "🚀 Compare Policies"}
          </button>
        </div>

        {error && (
          <p className="text-red-500 text-center mt-4 font-medium">{error}</p>
        )}
      </div>
    </div>
  );
}
