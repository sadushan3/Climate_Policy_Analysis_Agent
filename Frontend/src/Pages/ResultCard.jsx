import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function ResultCard() {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result;

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">
          ⚠ No result found. Please go back and compare again.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10 flex justify-center">
      <div className="bg-white shadow-lg rounded-2xl p-10 max-w-5xl w-full">
        <h2 className="text-3xl font-extrabold text-gray-800 mb-6 text-center">
          Policy Comparison Results
        </h2>

        {/* Similarity Score */}
        <div className="bg-blue-50 p-6 rounded-xl text-center mb-8">
          <p className="text-gray-600 text-lg font-medium">Similarity Score</p>
          <p className="text-6xl font-extrabold text-blue-600">
            {(result.similarity_score * 100).toFixed(0)}%
          </p>
        </div>

        {/* Overlap */}
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-800 mb-3">✅ Overlap</h3>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            {result.details.overlap.length > 0 ? (
              result.details.overlap.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))
            ) : (
              <li className="text-gray-400 italic">No overlaps found</li>
            )}
          </ul>
        </section>

        {/* Unique to Policy A */}
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-indigo-600 mb-3">
            Unique to Policy A
          </h3>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            {result.details.unique_policy1.length > 0 ? (
              result.details.unique_policy1.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))
            ) : (
              <li className="text-gray-400 italic">None</li>
            )}
          </ul>
        </section>

        {/* Unique to Policy B */}
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-purple-600 mb-3">
            Unique to Policy B
          </h3>
          <ul className="list-disc list-inside text-gray-700 space-y-2">
            {result.details.unique_policy2.length > 0 ? (
              result.details.unique_policy2.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))
            ) : (
              <li className="text-gray-400 italic">None</li>
            )}
          </ul>
        </section>

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
          >
            🔙 Go Back
          </button>
        </div>
      </div>
    </div>
  );
}
