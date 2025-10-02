import React, { useState } from 'react';
import { ArrowLeft, Download, FileText, TrendingUp, Users, CheckCircle, AlertCircle } from 'lucide-react';

export default function AnalysisResult() {
  // Mock result data for demonstration
  const [result] = useState({
    statistics: {
      word_count: 2847,
      sentence_count: 142,
      average_words_per_sentence: 20.05
    },
    comparison: {
      similarity_score: 0.75,
      details: {
        overlap: ['Data Protection', 'Privacy Rights', 'User Consent', 'Security Measures', 'Data Retention'],
        unique_policy1: ['GDPR Compliance', 'Right to be Forgotten', 'Data Portability'],
        unique_policy2: ['Cookie Policy', 'Third-party Sharing', 'Marketing Communications']
      }
    },
    policies: {
      policy1: {
        summary: 'This policy focuses on comprehensive data protection and user privacy rights, emphasizing GDPR compliance and transparent data handling practices.'
      },
      policy2: {
        summary: 'This policy outlines data usage for marketing purposes, third-party integrations, and cookie management with user consent mechanisms.'
      }
    },
    entities: [
      { label: 'Organization', text: 'European Commission' },
      { label: 'Regulation', text: 'GDPR' },
      { label: 'Date', text: '2018-05-25' },
      { label: 'Location', text: 'European Union' }
    ],
    recommendations: {
      compliance_gaps: ['Implement stricter data retention policies', 'Update cookie consent mechanisms'],
      priority: 'High',
      next_steps: ['Review third-party data sharing agreements', 'Conduct privacy impact assessment']
    }
  });

  const handleUploadClick = () => {
    alert('Navigate to upload page');
  };

  const comparison = result.comparison || {
    similarity_score: result.similarity_score,
    details: result.details,
  };

  const simScore = ((comparison?.similarity_score || 0) * 100).toFixed(0);
  const overlap = comparison?.details?.overlap || [];
  const unique1 = comparison?.details?.unique_policy1 || [];
  const unique2 = comparison?.details?.unique_policy2 || [];

  const getScoreColor = (score) => {
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 60) return 'from-blue-500 to-indigo-600';
    if (score >= 40) return 'from-amber-500 to-orange-600';
    return 'from-red-500 to-rose-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent">
              Analysis Results
            </h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleUploadClick}
              className="flex items-center gap-2 px-5 py-2.5 bg-white text-indigo-700 rounded-xl hover:bg-indigo-50 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              Upload Another
            </button>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
            >
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {result.statistics && (
            <>
              <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-200 border border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Word Count</h3>
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-gray-800">{result.statistics.word_count?.toLocaleString() || 'N/A'}</p>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-200 border border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Sentences</h3>
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-purple-600" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-gray-800">{result.statistics.sentence_count?.toLocaleString() || 'N/A'}</p>
              </div>
              <div className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-shadow duration-200 border border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">Avg Words/Sentence</h3>
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Users className="w-5 h-5 text-indigo-600" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-gray-800">{result.statistics.average_words_per_sentence || 'N/A'}</p>
              </div>
            </>
          )}
        </div>

        {/* Policy Comparison */}
        <div className="bg-white rounded-2xl p-8 shadow-lg mb-8 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-white" />
            </div>
            Policy Comparison
          </h2>

          {/* Similarity Score */}
          <div className={`mb-8 p-8 bg-gradient-to-r ${getScoreColor(simScore)} rounded-2xl text-white shadow-xl`}>
            <div className="flex items-end justify-between">
              <div>
                <h3 className="text-lg font-medium mb-2 opacity-90">Similarity Score</h3>
                <div className="text-7xl font-bold tracking-tight">{simScore}%</div>
              </div>
              <div className="w-32 h-32 bg-white bg-opacity-20 rounded-full flex items-center justify-center backdrop-blur-sm">
                <TrendingUp className="w-16 h-16 text-white" />
              </div>
            </div>
          </div>

          {/* Shared Elements */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              Shared Elements
              <span className="text-sm font-normal text-gray-500">({overlap.length})</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {overlap.length > 0 ? (
                overlap.map((el, idx) => (
                  <span key={idx} className="px-4 py-2 bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 border border-green-200 rounded-xl text-sm font-medium shadow-sm hover:shadow-md transition-shadow">
                    {el}
                  </span>
                ))
              ) : (
                <p className="text-gray-400 italic">No shared elements found</p>
              )}
            </div>
          </div>

          {/* Unique Elements */}
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6 border border-indigo-100">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                Unique to Policy 1
                <span className="text-sm font-normal text-gray-500">({unique1.length})</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {unique1.length > 0 ? (
                  unique1.map((el, idx) => (
                    <span key={idx} className="px-4 py-2 bg-white text-indigo-700 border border-indigo-200 rounded-lg text-sm font-medium shadow-sm">
                      {el}
                    </span>
                  ))
                ) : (
                  <p className="text-gray-400 italic">No unique elements</p>
                )}
              </div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                Unique to Policy 2
                <span className="text-sm font-normal text-gray-500">({unique2.length})</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {unique2.length > 0 ? (
                  unique2.map((el, idx) => (
                    <span key={idx} className="px-4 py-2 bg-white text-purple-700 border border-purple-200 rounded-lg text-sm font-medium shadow-sm">
                      {el}
                    </span>
                  ))
                ) : (
                  <p className="text-gray-400 italic">No unique elements</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Policy Summaries */}
        <div className="bg-white rounded-2xl p-8 shadow-lg mb-8 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Policy Summaries</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
              <h3 className="font-semibold text-gray-800 mb-3 text-lg">Policy 1</h3>
              <p className="text-gray-700 leading-relaxed">{result.policies?.policy1?.summary || "No summary available"}</p>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100">
              <h3 className="font-semibold text-gray-800 mb-3 text-lg">Policy 2</h3>
              <p className="text-gray-700 leading-relaxed">{result.policies?.policy2?.summary || "No summary available"}</p>
            </div>
          </div>
        </div>

        {/* Entities */}
        <div className="bg-white rounded-2xl p-8 shadow-lg mb-8 border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Extracted Entities</h2>
          <div className="flex flex-wrap gap-3">
            {Array.isArray(result.entities) && result.entities.length > 0 ? (
              result.entities.map((ent, idx) => (
                <span key={idx} className="px-4 py-2 bg-gradient-to-r from-amber-50 to-yellow-50 text-amber-800 border border-amber-200 rounded-xl text-sm font-medium shadow-sm hover:shadow-md transition-shadow">
                  <span className="font-semibold">{ent.label}:</span> {ent.text}
                </span>
              ))
            ) : (
              <p className="text-gray-400 italic">No entities found</p>
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Recommendations</h2>
          {result.recommendations ? (
            <div className="space-y-6">
              {/* Priority Badge */}
              {result.recommendations.priority && (
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-600">Priority:</span>
                  <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${
                    result.recommendations.priority === 'High' 
                      ? 'bg-red-100 text-red-700 border border-red-200' 
                      : result.recommendations.priority === 'Medium'
                      ? 'bg-amber-100 text-amber-700 border border-amber-200'
                      : 'bg-green-100 text-green-700 border border-green-200'
                  }`}>
                    {result.recommendations.priority}
                  </span>
                </div>
              )}

              {/* Compliance Gaps */}
              {result.recommendations.compliance_gaps && result.recommendations.compliance_gaps.length > 0 && (
                <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-xl p-6 border border-red-100">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-600" />
                    Compliance Gaps
                  </h3>
                  <ul className="space-y-3">
                    {result.recommendations.compliance_gaps.map((gap, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <span className="w-6 h-6 bg-red-100 text-red-700 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="text-gray-700 leading-relaxed">{gap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Next Steps */}
              {result.recommendations.next_steps && result.recommendations.next_steps.length > 0 && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-blue-600" />
                    Next Steps
                  </h3>
                  <ul className="space-y-3">
                    {result.recommendations.next_steps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="text-gray-700 leading-relaxed">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-400 italic">No recommendations generated</p>
          )}
        </div>
      </div>
    </div>
  );
}