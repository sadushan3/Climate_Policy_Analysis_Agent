import React, { useState } from 'react';
import axios from 'axios';
import Loading from '../components/Loading';
import { useNavigate } from 'react-router-dom';

export default function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    if (
      !selectedFile.type.match('application/pdf') &&
      !selectedFile.type.match('application/msword') &&
      !selectedFile.type.match('application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    ) {
      setError('Please upload a PDF or Word document');
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const resp = await axios.post(
        'http://127.0.0.1:8000/api/policy/full-analysis',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data', Accept: 'application/json' } }
      );

      const data = resp?.data;

      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format (not JSON)');
      }
      if (data.detail) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Server returned an error');
      }

      // Normalize response into a "comparison" object so frontend works with both formats
      const normalized = {
        ...data,
        comparison: data.comparison || {
          similarity_score: data.similarity_score,
          details: data.details,
        },
      };

      if (!normalized.document_name || !normalized.comparison) {
        console.warn('Full analysis raw response:', data);
        throw new Error('Invalid full analysis response format');
      }

      navigate('/analysis-result', { state: { result: normalized } });
    } catch (err) {
      console.error('Upload error:', err);
      const errorDetail = err.response?.data?.detail;
      let msg = 'Error processing document';
      if (Array.isArray(errorDetail)) msg = errorDetail.map(e => e.msg).join('\n');
      else if (typeof errorDetail === 'string') msg = errorDetail;
      else if (err.message) msg = err.message;
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white shadow-xl rounded-2xl p-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">Document Analysis</h1>
          <p className="text-lg text-gray-600">Upload your policy document and get detailed insights powered by AI</p>
        </div>

        <div className="mb-12">
          <div className="max-w-xl mx-auto">
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-lg font-medium text-gray-800">Drop your file here</p>
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

        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className={`px-8 py-3 text-white rounded-xl font-medium shadow-lg transition transform hover:scale-105 ${
              !file || loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700'
            }`}
          >
            {loading ? 'Analyzing...' : '🔍 Analyze Document'}
          </button>

          {loading && <Loading />}
          {error && <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-medium">{error}</div>}
        </div>
      </div>
    </div>
  );
}
