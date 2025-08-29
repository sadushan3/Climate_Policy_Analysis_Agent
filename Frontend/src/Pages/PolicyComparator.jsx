import React, { useState } from "react";

// Dummy comparePolicies function for demonstration
async function comparePolicies(policy1, policy2) {
  // Simulate API call
  return new Promise((resolve) =>
    setTimeout(() => resolve({ data: `Comparison between:\n${policy1}\n\nand\n\n${policy2}` }), 1200)
  );
}

function ResultCard({ result }) {
  return (
    <div className="mt-8 bg-gray-800 rounded-xl shadow-lg p-6 border border-blue-400">
      <h2 className="text-xl font-semibold mb-2 text-blue-300">Comparison Result</h2>
      <pre className="whitespace-pre-wrap text-gray-200">{result}</pre>
    </div>
  );
}

export default function PolicyComparator() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    setError("");
    setResult(null);
    if (!policy1.trim() || !policy2.trim()) {
      setError("⚠️ Please enter both policies before comparing.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await comparePolicies(policy1, policy2);
      setResult(data);
    } catch {
      setError("❌ Failed to compare policies (check backend).");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-800 px-4">
      <div className="w-full max-w-3xl bg-gray-900 rounded-2xl shadow-2xl p-8 mt-8">
        <h1 className="text-4xl font-extrabold mb-8 text-center text-blue-300 drop-shadow">
          📑 Policy Comparator
        </h1>
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium mb-2 text-blue-200">Policy 1</label>
            <textarea
              placeholder="Paste or type Policy 1..."
              value={policy1}
              onChange={(e) => setPolicy1(e.target.value)}
              className="w-full p-4 bg-gray-800 rounded-lg min-h-[180px] resize-none border-2 border-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2 text-blue-200">Policy 2</label>
            <textarea
              placeholder="Paste or type Policy 2..."
              value={policy2}
              onChange={(e) => setPolicy2(e.target.value)}
              className="w-full p-4 bg-gray-800 rounded-lg min-h-[180px] resize-none border-2 border-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
            />
          </div>
        </div>

        {error && (
          <div className="text-red-400 text-center font-semibold mb-4">{error}</div>
        )}

        <div className="flex justify-center">
          <button
            onClick={handleCompare}
            disabled={loading}
            className="px-8 py-3 bg-gradient-to-r from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 rounded-xl font-bold text-lg text-white shadow-lg transition disabled:opacity-50"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                </svg>
                Comparing...
              </span>
            ) : (
              "Compare Policies 🚀"
            )}
          </button>
        </div>

        {result && <ResultCard result={result} />}
      </div>
    </div>
  );
}