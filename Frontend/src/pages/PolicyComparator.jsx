import { useState } from "react";
import { comparePolicies } from "../api";
import ResultCard from "./ResultCard";

export default function PolicyComparator() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    setError("");
    if (!policy1 || !policy2) {
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
    <div className="p-6 bg-gray-900 min-h-screen text-white">
      <h1 className="text-3xl font-bold mb-6 text-center">
        📑 Policy Comparator
      </h1>
      <div className="grid md:grid-cols-2 gap-4">
        <textarea
          placeholder="Enter Policy 1..."
          value={policy1}
          onChange={(e) => setPolicy1(e.target.value)}
          className="p-4 bg-gray-800 rounded-lg min-h-[200px] resize-none"
        />
        <textarea
          placeholder="Enter Policy 2..."
          value={policy2}
          onChange={(e) => setPolicy2(e.target.value)}
          className="p-4 bg-gray-800 rounded-lg min-h-[200px] resize-none"
        />
      </div>

      {error && <p className="text-red-400 text-sm mt-4">{error}</p>}

      <div className="flex justify-center mt-6">
        <button
          onClick={handleCompare}
          disabled={loading}
          className="px-6 py-3 bg-blue-500 hover:bg-blue-600 rounded-lg font-semibold disabled:opacity-50"
        >
          {loading ? "Comparing..." : "Compare Policies 🚀"}
        </button>
      </div>

      {result && <ResultCard result={result} />}
    </div>
  );
}
