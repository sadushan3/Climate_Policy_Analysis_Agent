import React, { useState } from "react";

function ResultPage({ result, onBack }) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <h1 className="text-lg font-bold text-blue-600">PolicyCompare</h1>
          <nav className="space-x-6 text-gray-600 font-medium">
            <a href="#">Home</a>
            <a href="#">Compare</a>
            <a href="#">About</a>
          </nav>
          <button className="w-8 h-8 rounded-full overflow-hidden border">
            <img
              src="https://i.pravatar.cc/40"
              alt="profile"
              className="w-full h-full"
            />
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-5xl mx-auto px-6 py-10">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Policy Comparison Results
        </h2>
        <p className="text-gray-600 mb-6">
          Review the detailed comparison between Policy A and Policy B.
        </p>

        {/* Similarity Score */}
        <div className="bg-blue-50 rounded-xl p-6 text-center mb-10">
          <p className="text-lg text-gray-700 font-medium">Similarity Score</p>
          <h3 className="text-5xl font-extrabold text-blue-600 mt-2">
            {(result.similarity_score * 100).toFixed(0)}%
          </h3>
          <span className="text-sm text-gray-500">Comparing</span>
        </div>

        {/* Overlap Section */}
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
            ✅ Overlap
          </h3>
          <p className="text-gray-600 mb-4">
            These are the terms and conditions similar between Policy A and B.
          </p>
          <div className="space-y-3">
            {result.details.overlap.map((item, i) => (
              <div
                key={i}
                className="flex justify-between bg-white shadow-sm border rounded-lg px-4 py-3"
              >
                <span className="font-medium text-gray-700">{item}</span>
                <span className="text-gray-600">
                  Both policies cover {item}.
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Unique Policy A */}
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-800">
            Unique to <span className="text-blue-600">Policy A</span>
          </h3>
          <p className="text-gray-600 mb-4">
            These features are only found in Policy A.
          </p>
          <ul className="space-y-3">
            {result.details.unique_policy1.map((item, i) => (
              <li
                key={i}
                className="bg-white shadow-sm border rounded-lg px-4 py-3"
              >
                <span className="font-medium text-gray-700">{item}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Unique Policy B */}
        <section className="mb-10">
          <h3 className="text-xl font-semibold text-gray-800">
            Unique to <span className="text-blue-600">Policy B</span>
          </h3>
          <p className="text-gray-600 mb-4">
            These features are only found in Policy B.
          </p>
          <ul className="space-y-3">
            {result.details.unique_policy2.map((item, i) => (
              <li
                key={i}
                className="bg-white shadow-sm border rounded-lg px-4 py-3"
              >
                <span className="font-medium text-gray-700">{item}</span>
              </li>
            ))}
          </ul>
        </section>

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={onBack}
            className="px-6 py-3 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 transition"
          >
            Compare Again
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 py-4 text-center text-sm text-gray-500 mt-10">
        © 2024 PolicyCompare. All rights reserved. | Privacy Policy | Terms of
        Service
      </footer>
    </div>
  );
}

export default ResultPage;
