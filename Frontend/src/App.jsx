import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import PolicyComparator from "./Pages/PolicyComparator";
import ResultCard from "./pages/Resultcard";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        {/* Home: Compare policies */}
        <Route path="/" element={<PolicyComparator />} />

        {/* Result page */}
        <Route path="/result" element={<ResultCard />} />
      </Routes>
    </Router>
  );
}

export default App;
