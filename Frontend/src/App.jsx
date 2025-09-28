import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import PolicyComparator from './Pages/PolicyComparator';
import ResultPage from './pages/Resultcard';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<PolicyComparator />} />
        <Route path="/result" element={<ResultPage />} />
      </Routes>
    </Router>
  );
}

export default App;
