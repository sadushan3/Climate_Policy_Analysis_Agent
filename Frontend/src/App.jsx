import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DocumentUpload from './Pages/DocumentUpload';
import AnalysisResult from './pages/AnalysisResult';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/upload" />} />
        <Route path="/upload" element={<DocumentUpload />} />
        <Route path="/analysis-result" element={<AnalysisResult />} />
      </Routes>
    </Router>
  );
}

export default App;
