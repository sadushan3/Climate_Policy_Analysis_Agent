import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function AnalysisResult() {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result;

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-gray-600 text-lg">⚠ No analysis results found</p>
          <button
            onClick={() => navigate('/upload')}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Upload Document
          </button>
        </div>
      </div>
    );
  }

  // Always normalize comparison
  const comparison = result.comparison || {
    similarity_score: result.similarity_score,
    details: result.details,
  };

  const simScore = ((comparison?.similarity_score || 0) * 100).toFixed(0);
  const overlap = comparison?.details?.overlap || [];
  const unique1 = comparison?.details?.unique_policy1 || [];
  const unique2 = comparison?.details?.unique_policy2 || [];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">Analysis Results</h1>
        <div className="flex space-x-4">
          <button
            onClick={() => navigate('/upload')}
            className="px-4 py-2 text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition"
          >
            ← Upload Another Document
          </button>
          <button
            onClick={() => window.print()}
            className="px-4 py-2 text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition"
          >
            📄 Export Report
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="bg-white rounded-xl p-6 shadow-md mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Document Statistics</h2>
        {result.statistics ? (
          <ul className="list-disc pl-6 text-gray-700 space-y-1">
            <li>Word Count: {result.statistics.word_count || 'N/A'}</li>
            <li>Sentence Count: {result.statistics.sentence_count || 'N/A'}</li>
            <li>Average Words/Sentence: {result.statistics.average_words_per_sentence || 'N/A'}</li>
          </ul>
        ) : (
          <p className="text-gray-500 italic">No statistics available</p>
        )}
      </div>

      {/* Policy Comparison Section */}
      <div className="bg-white rounded-xl p-6 shadow-md mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Policy Comparison</h2>

        {/* Similarity Score */}
        <div className="mb-8 p-6 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl text-white">
          <h3 className="text-xl font-medium mb-2">Similarity Score</h3>
          <div className="text-6xl font-bold">{simScore}%</div>
        </div>

        {/* Shared Elements */}
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-800 mb-2">Shared Elements</h3>
          <div className="flex flex-wrap gap-2">
            {overlap.length > 0 ? (
              overlap.map((el, idx) => (
                <span key={idx} className="px-3 py-1 bg-green-50 text-green-700 border border-green-200 rounded-lg text-sm">
                  {el}
                </span>
              ))
            ) : (
              <p className="text-gray-500 italic">No shared elements found</p>
            )}
          </div>
        </div>

        {/* Unique Elements */}
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">Unique to Policy 1</h3>
            <div className="flex flex-wrap gap-2">
              {unique1.length > 0 ? (
                unique1.map((el, idx) => (
                  <span key={idx} className="px-3 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-sm">
                    {el}
                  </span>
                ))
              ) : (
                <p className="text-gray-500 italic">No unique elements</p>
              )}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">Unique to Policy 2</h3>
            <div className="flex flex-wrap gap-2">
              {unique2.length > 0 ? (
                unique2.map((el, idx) => (
                  <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 border border-purple-200 rounded-lg text-sm">
                    {el}
                  </span>
                ))
              ) : (
                <p className="text-gray-500 italic">No unique elements</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Policy Summaries */}
      <div className="bg-white rounded-xl p-6 shadow-md mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Policy Summaries</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Policy 1</h3>
            <p className="text-gray-600">{result.policies?.policy1?.summary || "No summary available"}</p>
          </div>
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Policy 2</h3>
            <p className="text-gray-600">{result.policies?.policy2?.summary || "No summary available"}</p>
          </div>
        </div>
      </div>

      {/* Entities */}
      <div className="bg-white rounded-xl p-6 shadow-md mb-8">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Extracted Entities</h2>
        <div className="flex flex-wrap gap-2">
          {Array.isArray(result.entities) && result.entities.length > 0 ? (
            result.entities.map((ent, idx) => (
              <span key={idx} className="px-3 py-1 bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-lg text-sm">
                {ent.label}: {ent.text}
              </span>
            ))
          ) : (
            <p className="text-gray-500 italic">No entities found</p>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-xl p-6 shadow-md">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Recommendations</h2>
        {result.recommendations ? (
          <pre className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(result.recommendations, null, 2)}
          </pre>
        ) : (
          <p className="text-gray-500 italic">No recommendations generated</p>
        )}
      </div>
    </div>
  );
}
