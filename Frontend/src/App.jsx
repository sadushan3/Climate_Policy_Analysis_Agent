import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PolicyComparator from './pages/PolicyComparator';
import ResultCard from './pages/Resultcard';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<PolicyComparator />} />
        <Route path="/result" element={<ResultCard />} />
      </Routes>
    </Router>
  );
}

export default App;
