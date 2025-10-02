import React, { useState } from 'react';
import axios from 'axios';
import Loading from '../components/Loading';
import { useNavigate } from 'react-router-dom';

export default function DocumentAnalysis() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisType, setAnalysisType] = useState('full'); // full, summarize, ner
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }
    setFile(selectedFile);
    setError('');
  };

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please select a file to analyze');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      let endpoint = '';
      switch (analysisType) {
        case 'full':
          endpoint = 'http://127.0.0.1:8000/api/policy/full-analysis';
          break;
        case 'summarize':
          endpoint = 'http://127.0.0.1:8000/api/policy/summarize';
          break;
        case 'ner':
          endpoint = 'http://127.0.0.1:8000/api/policy/ner';
          break;
        default:
          endpoint = 'http://127.0.0.1:8000/api/policy/analyze';
      }

      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Check if we got a proper JSON response
      if (response.data instanceof Blob || typeof response.data === 'string') {
        throw new Error('Invalid response format. Expected JSON but received raw file data.');
      }

      // Validate the response based on analysis type
      switch (analysisType) {
        case 'full':
          if (!response.data.document_name || !response.data.analysis) {
            throw new Error('Invalid full analysis response format');
          }
          break;
        case 'summarize':
          if (!response.data.summary) {
            throw new Error('Invalid summary response format');
          }
          break;
        case 'ner':
          if (!response.data.entities) {
            throw new Error('Invalid NER response format');
          }
          break;
        default:
          if (!response.data.analysis) {
            throw new Error('Invalid analysis response format');
          }
      }

      // Navigate to the results page with the analysis data
      navigate('/analysis-result', { state: { result: response.data, type: analysisType } });
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analyzing document');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const analysisOptions = [
    {
      id: 'full',
      label: 'Full Analysis',
      description: 'Complete policy analysis with climate factors, comparisons, and recommendations',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
    },
    {
      id: 'summarize',
      label: 'Generate Summary',
      description: 'Create a concise summary of the policy document',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 6h16M4 12h16m-7 6h7" />
        </svg>
      ),
    },
    {
      id: 'ner',
      label: 'Extract Entities',
      description: 'Identify and extract key entities from the document',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
        </svg>
      ),
    },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white shadow-xl rounded-2xl p-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Document Analysis
          </h1>
          <p className="text-lg text-gray-600">
            Upload your policy document and get detailed insights powered by AI
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-12">
          <div className="max-w-xl mx-auto">
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center space-y-4"
              >
                <div className="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg font-medium text-gray-800">Drop your PDF file here</p>
                  <p className="text-sm text-gray-500 mt-1">or click to browse from your computer</p>
                </div>
              </label>
              {file && (
                <div className="mt-4 p-4 bg-indigo-50 rounded-lg inline-flex items-center">
                  <svg className="w-6 h-6 text-indigo-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-indigo-600 font-medium">{file.name}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Analysis Options */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {analysisOptions.map((option) => (
            <div
              key={option.id}
              onClick={() => setAnalysisType(option.id)}
              className={`cursor-pointer rounded-xl p-6 border-2 transition-all ${
                analysisType === option.id
                  ? 'border-indigo-600 bg-indigo-50'
                  : 'border-gray-200 hover:border-indigo-200'
              }`}
            >
              <div
                className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                  analysisType === option.id
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {option.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                {option.label}
              </h3>
              <p className="text-sm text-gray-600">{option.description}</p>
            </div>
          ))}
        </div>

        {/* Action Section */}
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={handleAnalyze}
            disabled={!file || loading}
            className={`px-8 py-3 text-white rounded-xl font-medium shadow-lg transition transform hover:scale-105 ${
              !file || loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
            } disabled:opacity-50 disabled:transform-none`}
          >
            {loading ? 'Analyzing...' : '🔍 Analyze Document'}
          </button>

          {loading && <Loading />}

          {error && (
            <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-medium">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="mt-16 grid md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Smart Analysis</h3>
          <p className="text-gray-600">AI-powered document analysis to extract key insights and policy details.</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Climate Focus</h3>
          <p className="text-gray-600">Specialized analysis of climate-related factors and environmental impacts.</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-md">
          <div className="w-10 h-10 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-4">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Comprehensive Reports</h3>
          <p className="text-gray-600">Detailed analysis reports with actionable recommendations and insights.</p>
        </div>
      </div>
    </div>
  );
}
