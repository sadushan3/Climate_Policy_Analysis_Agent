import React from "react";
export default function ResultCard({ result }) {
  if (!result) return null; // Prevent rendering if result is undefined

  return (
    <div className="mt-8 bg-gray-800 p-6 rounded-xl shadow-lg">
      <h2 className="text-xl font-bold mb-4">🔎 Comparison Result</h2>
      <div className="mb-4">
        <p className="text-lg">
          Similarity Score:{" "}
          <span className="font-bold text-blue-400">
            {(result.similarity_score * 100).toFixed(2)}%
          </span>
        </p>
        <div className="w-full bg-gray-700 h-4 rounded-lg mt-2">
          <div
            className="h-4 bg-blue-500 rounded-lg transition-all duration-500"
            style={{ width: `${result.similarity_score * 100}%` }}
          />
        </div>
      </div>
      <div className="grid md:grid-cols-3 gap-6">
        <div>
          <h3 className="font-semibold text-green-400 mb-2">✅ Overlap</h3>
          <ul className="list-disc list-inside text-gray-300">
            {result.details.overlap.length > 0 ? (
              result.details.overlap.map((w, i) => <li key={i}>{w}</li>)
            ) : (
              <li className="text-gray-500">None</li>
            )}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold text-yellow-400 mb-2">
            📌 Unique Policy 1
          </h3>
          <ul className="list-disc list-inside text-gray-300">
            {result.details.unique_policy1.length > 0 ? (
              result.details.unique_policy1.map((w, i) => <li key={i}>{w}</li>)
            ) : (
              <li className="text-gray-500">None</li>
            )}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold text-red-400 mb-2">
            📌 Unique Policy 2
          </h3>
          <ul className="list-disc list-inside text-gray-300">
            {result.details.unique_policy2.length > 0 ? (
              result.details.unique_policy2.map((w, i) => <li key={i}>{w}</li>)
            ) : (
              <li className="text-gray-500">None</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}