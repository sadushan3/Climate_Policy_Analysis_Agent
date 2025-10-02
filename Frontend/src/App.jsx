import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

import Navbar from "./components/Navbar";
import PolicyAnalyzer from "./Pages/DocumentAnalysis"; // Upload & analyze page
import ResultPage from "./Pages/ResultPage";           // Page to display results
import AnalysisCharts from "./Pages/AnalysisCharts";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
        <Navbar />

        <main className="container mx-auto px-4 py-8 flex-1">
          <Routes>
            {/* Redirect root "/" to "/upload" */}
            <Route path="/" element={<Navigate to="/upload" />} />

            {/* Upload/Analyzer page */}
            <Route path="/upload" element={<PolicyAnalyzer />} />

            {/* Result page */}
            <Route path="/result" element={<ResultPage />} />

            <Route path="/charts" element={<AnalysisCharts />} />
          </Routes>
        </main>

        <footer className="text-center py-6 text-gray-600 text-sm">
          © 2025 Climate Policy Analysis. All rights reserved.
        </footer>
      </div>
    </Router>
  );
}

export default App;
