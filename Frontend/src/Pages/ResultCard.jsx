import React from "react";
import { useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

export default function ResultCard() {
  const location = useLocation();
  const result = location.state?.result;

  if (!result) return null;

  return (
    <div className="h-screen w-full bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300 overflow-hidden flex items-center justify-center">
      <AnimatePresence>
        <motion.div
          key="result-card"
          initial={{ opacity: 0, y: 50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 50, scale: 0.95 }}
          transition={{ duration: 0.6, type: "spring" }}
          className="w-full max-w-4xl p-8 bg-gradient-to-br from-blue-100 via-blue-200 to-blue-300 rounded-3xl shadow-xl border border-blue-400"
        >
          {/* Header Section */}
          <motion.h2
            className="text-4xl font-semibold text-gray-800 mb-8 text-center tracking-wide"
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            🔎 Comparison Result
          </motion.h2>

          {/* Similarity Score Section */}
          <div className="mb-8">
            <motion.p
              className="text-2xl text-gray-800 mb-4"
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              Similarity Score:{" "}
              <span className="font-bold text-teal-600">
                {(result.similarity_score * 100).toFixed(2)}%
              </span>
            </motion.p>

            <div className="w-full bg-gray-300 h-4 rounded-xl mt-4 overflow-hidden">
              <motion.div
                className="h-4 bg-gradient-to-r from-teal-500 to-teal-400 rounded-xl"
                initial={{ width: 0 }}
                animate={{ width: `${result.similarity_score * 100}%` }}
                transition={{ duration: 1, type: "spring" }}
              />
            </div>
          </div>

          {/* Details Section */}
          <motion.div
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: {},
              visible: {
                transition: {
                  staggerChildren: 0.15,
                },
              },
            }}
          >
            {[
              {
                title: "✅ Overlap",
                items: result.details.overlap,
                color: "teal-500",
                hoverColor: "teal-600",
                shadowColor: "#4fd1c533",
              },
              {
                title: "📌 Unique Policy 1",
                items: result.details.unique_policy1,
                color: "blue-500",
                hoverColor: "blue-600",
                shadowColor: "#63b3ed33",
              },
              {
                title: "📌 Unique Policy 2",
                items: result.details.unique_policy2,
                color: "purple-500",
                hoverColor: "purple-600",
                shadowColor: "#9f7aea33",
              },
            ].map((section, idx) => (
              <motion.div
                key={idx}
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
                whileHover={{
                  scale: 1.05,
                  boxShadow: `0 0 24px ${section.shadowColor}`,
                }}
                className="bg-white p-6 rounded-xl border border-gray-300 hover:bg-gray-50 transition-colors"
              >
                <h3
                  className={`font-semibold mb-4 text-${section.color} text-2xl`}
                >
                  {section.title}
                </h3>
                <ul className="list-disc list-inside text-gray-600">
                  {section.items.length > 0 ? (
                    section.items.map((item, i) => (
                      <motion.li
                        key={i}
                        whileHover={{
                          scale: 1.08,
                        }}
                        transition={{ type: "spring", stiffness: 300 }}
                        className={`hover:text-${section.hoverColor}`}
                      >
                        {item}
                      </motion.li>
                    ))
                  ) : (
                    <li className="text-gray-400 italic">None</li>
                  )}
                </ul>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
