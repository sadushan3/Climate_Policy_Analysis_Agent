import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function AnalysisPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { analysis } = location.state || {};

  if (!analysis) {
    navigate("/");
    return null;
  }

  // Example: Unique vs Overlap words count
  const data = {
    labels: ["Unique Policy 1", "Overlap", "Unique Policy 2"],
    datasets: [
      {
        label: "Number of Words",
        data: [
          analysis.details.unique_policy1.length,
          analysis.details.overlap.length,
          analysis.details.unique_policy2.length
        ],
        backgroundColor: ["#3b82f6", "#8b5cf6", "#10b981"]
      }
    ]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Policy Word Comparison" }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">Analysis Charts</h1>
      <div className="bg-white p-6 rounded-xl shadow-md">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}
