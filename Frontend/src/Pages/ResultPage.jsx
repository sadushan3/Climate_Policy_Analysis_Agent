import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { analysis } = location.state || {};

  // If no analysis data, redirect to upload
  if (!analysis) {
    navigate("/upload");
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-600 to-indigo-600 p-2 rounded-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Analysis Results</h1>
              <p className="text-xs text-gray-500">{analysis.document_name}</p>
            </div>
          </div>
          <button
            onClick={() => navigate("/upload")}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 transition-colors"
          >
            New Analysis
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Overview */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {analysis.statistics.word_count}
            </p>
            <p className="text-sm text-gray-600 mt-1">Total Words</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">
              {analysis.statistics.sentence_count}
            </p>
            <p className="text-sm text-gray-600 mt-1">Sentences</p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <svg
                className="w-8 h-8 text-purple-600"
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
            <p className="text-3xl font-bold text-gray-900">
              {analysis.statistics.average_words_per_sentence.toFixed(1)}
            </p>
            <p className="text-sm text-gray-600 mt-1">Avg Words/Sentence</p>
          </div>

          <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl p-6 shadow-md text-white">
            <div className="flex items-center justify-between mb-2">
              <svg
                className="w-8 h-8"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
            <p className="text-3xl font-bold">
              {(analysis.similarity_score * 100).toFixed(0)}%
            </p>
            <p className="text-sm opacity-90 mt-1">Similarity Score</p>
          </div>
        </div>

        {/* Policies Comparison */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {["policy1", "policy2"].map((p, idx) => (
            <div
              key={p}
              className="bg-white rounded-xl shadow-md border border-gray-100 overflow-hidden"
            >
              <div className="bg-gradient-to-r from-blue-500 to-indigo-500 p-4">
                <h3 className="text-lg font-bold text-white">Policy {idx + 1}</h3>
              </div>
              <div className="p-6">
                <p className="text-gray-700 mb-4">{analysis.policies[p].content}</p>
                <div className="bg-blue-50 rounded-lg p-4 mb-4">
                  <p className="text-sm font-semibold text-gray-900 mb-1">Summary</p>
                  <p className="text-sm text-gray-700">{analysis.policies[p].summary}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900 mb-2">Keywords</p>
                  <div className="flex flex-wrap gap-2">
                    {analysis.policies[p].keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Word Comparison */}
        <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Word Comparison</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                Unique to Policy 1
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysis.details.unique_policy1.map((word, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-white text-blue-700 rounded text-xs font-medium"
                  >
                    {word}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
              <h3 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-600 rounded-full"></div>
                Overlap
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysis.details.overlap.map((word, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-white text-purple-700 rounded text-xs font-medium"
                  >
                    {word}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                Unique to Policy 2
              </h3>
              <div className="flex flex-wrap gap-2">
                {analysis.details.unique_policy2.map((word, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-white text-green-700 rounded text-xs font-medium"
                  >
                    {word}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Named Entities */}
        {analysis.entities && analysis.entities.length > 0 && (
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Named Entities</h2>
            <div className="flex flex-wrap gap-3">
              {analysis.entities.map((ent, idx) => (
                <div
                  key={idx}
                  className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg px-4 py-2"
                >
                  <span className="text-xs font-semibold text-indigo-600 uppercase">
                    {ent.label}
                  </span>
                  <p className="text-sm font-medium text-gray-900 mt-1">{ent.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Weather Recommendations */}
        {analysis.recommendations && (
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"
                />
              </svg>
              Weather Recommendations
            </h2>

            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Predicted Condition</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analysis.recommendations.predicted_condition}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600 mb-1">Confidence</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {(analysis.recommendations.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>

            <h3 className="font-semibold text-lg text-gray-900 mb-4">Top Similar Days</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {analysis.recommendations.top_similar_days.map((day, idx) => (
                <div
                  key={idx}
                  className="bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <svg
                        className="w-4 h-4 text-gray-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                      </svg>
                      <span className="font-semibold text-gray-900">{day.location}</span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                      <span>{day.month}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="flex items-center gap-2">
                      <svg
                        className="w-4 h-4 text-red-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4"
                        />
                      </svg>
                      <span className="text-sm text-gray-900">{day.temperature}°C</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <svg
                        className="w-4 h-4 text-blue-500"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"
                        />
                      </svg>
                      <span className="text-sm text-gray-900">{day.condition}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600">{day.notes}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
