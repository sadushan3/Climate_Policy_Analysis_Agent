import React, { useState } from "react";

function PolicyResult({ result, onBack }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white shadow-lg rounded-2xl p-8 max-w-2xl w-full">
        <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">
          Comparison Result
        </h2>
        <pre className="bg-gray-100 p-4 rounded-md text-sm text-gray-700 whitespace-pre-wrap">
          {JSON.stringify(result, null, 2)}
        </pre>
        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="px-6 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}

function PolicyComparator({ onCompareSuccess }) {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCompare = async () => {
    setLoading(true);
    // Simulated API call
    await new Promise((res) => setTimeout(res, 1200));
    const simulatedResult = {
      summary:
        "Policy A covers environmental regulations more, Policy B is stronger on data privacy.",
      common_points: ["Risk assessment", "Compliance with laws"],
      differences: [
        "Policy A includes carbon footprint reporting",
        "Policy B has detailed data breach section",
      ],
    };
    onCompareSuccess(simulatedResult);
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white shadow-lg rounded-2xl p-8 max-w-4xl w-full">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-2">
          Climatic AI Policy Comparator
        </h1>
        <p className="text-center text-gray-500 mb-8">
          Simply paste your policy text or upload the documents to see a
          side-by-side comparison.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-gray-700 font-medium mb-2">
              Policy A
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-400 focus:outline-none"
              rows="6"
              value={policy1}
              onChange={(e) => setPolicy1(e.target.value)}
              placeholder="Paste the full text of the first policy here."
            />
            <div className="mt-3 flex items-center justify-center text-sm text-gray-500">
              <span className="mx-2">or</span>
              <label className="cursor-pointer px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition">
                Upload Document
                <input type="file" className="hidden" />
              </label>
            </div>
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-2">
              Policy B
            </label>
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-400 focus:outline-none"
              rows="6"
              value={policy2}
              onChange={(e) => setPolicy2(e.target.value)}
              placeholder="Paste the full text of the second policy here."
            />
            <div className="mt-3 flex items-center justify-center text-sm text-gray-500">
              <span className="mx-2">or</span>
              <label className="cursor-pointer px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition">
                Upload Document
                <input type="file" className="hidden" />
              </label>
            </div>
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={handleCompare}
            disabled={!policy1 || !policy2 || loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium shadow hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? "Comparing..." : "Compare Policies"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [result, setResult] = useState(null);

  return !result ? (
    <PolicyComparator onCompareSuccess={setResult} />
  ) : (
    <PolicyResult result={result} onBack={() => setResult(null)} />
  );
}
