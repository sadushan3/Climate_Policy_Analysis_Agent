import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Loading from "../components/Loading";

export default function ResultCard() {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result;
  const [activeTab, setActiveTab] = useState("overview");

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-gray-600 text-lg">
            ⚠ No comparison results found
          </p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Compare Policies
          </button>
        </div>
      </div>
    );
  }

  const renderBadges = (items, color) => {
    if (!items || items.length === 0) {
      return <span className="text-gray-400 italic">None</span>;
    }
    return (
      <div className="flex flex-wrap gap-2">
        {items.map((item, idx) => (
          <span
            key={idx}
            className={`px-4 py-2 rounded-lg text-sm font-medium bg-${color}-50 text-${color}-700 border border-${color}-200 shadow-sm`}
          >
            {item}
          </span>
        ))}
      </div>
    );
  };

  const TabButton = ({ id, label, icon }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition ${activeTab === id
        ? "bg-indigo-100 text-indigo-700 font-medium"
        : "text-gray-600 hover:bg-gray-100"}`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white shadow-xl rounded-2xl p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Policy Comparison Results
          </h1>
          <p className="text-gray-600">
            Detailed analysis and comparison of your climate policies
          </p>
        </div>

        {/* Similarity Score Card */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-8 text-white mb-8">
          <div className="grid md:grid-cols-2 gap-8">
            <div className="text-center md:text-left">
              <h3 className="text-xl font-medium mb-2">Similarity Score</h3>
              <div className="text-6xl font-bold">
                {(result.similarity_score * 100).toFixed(0)}%
              </div>
            </div>
            <div className="flex items-center justify-center md:justify-end">
              <div className="w-32 h-32 relative">
                <svg className="w-full h-full" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="rgba(255, 255, 255, 0.2)"
                    strokeWidth="3"
                  />
                  <path
                    d="M18 2.0845
                      a 15.9155 15.9155 0 0 1 0 31.831
                      a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#fff"
                    strokeWidth="3"
                    strokeDasharray={`${result.similarity_score * 100}, 100`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-2xl font-bold">
                  {(result.similarity_score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-8 overflow-x-auto pb-2">
          <TabButton
            id="overview"
            label="Overview"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            }
          />
          <TabButton
            id="details"
            label="Detailed Analysis"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            }
          />
          <TabButton
            id="recommendations"
            label="Recommendations"
            icon={
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            }
          />
        </div>

        {/* Content Sections */}
        <div className="space-y-8">
          {activeTab === "overview" && (
            <div className="grid md:grid-cols-2 gap-8">
              {/* Shared Elements */}
              <div className="bg-green-50 rounded-xl p-6 border border-green-200">
                <h3 className="text-lg font-semibold text-green-800 mb-4 flex items-center">
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Shared Elements
                </h3>
                {renderBadges(result.details.overlap, "green")}
              </div>

              {/* Summary Stats */}
              <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Summary Statistics</h3>
                <div className="space-y-4">
                  <div>
                    <div className="text-sm font-medium text-gray-600 mb-1">Shared Elements</div>
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-2 bg-green-500 rounded-full"
                        style={{
                          width: `${(result.details.overlap.length /
                            (result.details.overlap.length +
                              result.details.unique_policy1.length +
                              result.details.unique_policy2.length)) *
                            100
                            }%`,
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600 mb-1">Unique to Policy A</div>
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-2 bg-indigo-500 rounded-full"
                        style={{
                          width: `${(result.details.unique_policy1.length /
                            (result.details.overlap.length +
                              result.details.unique_policy1.length +
                              result.details.unique_policy2.length)) *
                            100
                            }%`,
                        }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-600 mb-1">Unique to Policy B</div>
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-2 bg-purple-500 rounded-full"
                        style={{
                          width: `${(result.details.unique_policy2.length /
                            (result.details.overlap.length +
                              result.details.unique_policy1.length +
                              result.details.unique_policy2.length)) *
                            100
                            }%`,
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "details" && (
            <div className="space-y-8">
              <section className="bg-indigo-50 rounded-xl p-6 border border-indigo-200">
                <h3 className="text-xl font-semibold text-indigo-800 mb-4">
                  Unique to Policy A
                </h3>
                {renderBadges(result.details.unique_policy1, "indigo")}
              </section>

              <section className="bg-purple-50 rounded-xl p-6 border border-purple-200">
                <h3 className="text-xl font-semibold text-purple-800 mb-4">
                  Unique to Policy B
                </h3>
                {renderBadges(result.details.unique_policy2, "purple")}
              </section>
            </div>
          )}

          {activeTab === "recommendations" && (
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">
                AI-Generated Recommendations
              </h3>
              <div className="space-y-4">
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-800 mb-2">🌱 Environmental Impact</h4>
                  <p className="text-gray-600">
                    Consider integrating the unique environmental protection measures from both
                    policies for a more comprehensive approach.
                  </p>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-800 mb-2">📊 Implementation Strategy</h4>
                  <p className="text-gray-600">
                    Combine the implementation timelines and resource allocation strategies
                    from both policies to create a more effective execution plan.
                  </p>
                </div>
                <div className="bg-white p-4 rounded-lg border border-gray-200">
                  <h4 className="font-medium text-gray-800 mb-2">🌍 Global Alignment</h4>
                  <p className="text-gray-600">
                    Align the combined policy with international climate agreements and
                    standards for better global cooperation.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center mt-8 space-x-4">
          <button
            onClick={() => window.print()}
            className="px-6 py-2 text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition"
          >
            📄 Export Report
          </button>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition"
          >
            Compare More Policies
          </button>
        </div>
      </div>
    </div>
  );
}
