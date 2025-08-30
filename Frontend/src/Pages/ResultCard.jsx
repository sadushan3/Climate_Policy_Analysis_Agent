import React from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function FullScreenResultCard({ result }) {
  if (!result) return null;

  return (
    <div className="h-screen w-full bg-gradient-to-br from-gray-800 via-gray-700 to-black overflow-hidden flex items-center justify-center relative">
      {/* Background Video */}
      <video
        autoPlay
        loop
        muted
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          zIndex: -1,
        }}
      >
        <source src="assets/ai.mp4" type="video/mp4" />
      </video>

      <AnimatePresence>
        <motion.div
          key="result-card"
          initial={{ opacity: 0, y: 50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 50, scale: 0.95 }}
          transition={{ duration: 0.6, type: "spring" }}
          className="w-full max-w-4xl p-8 bg-gradient-to-br from-indigo-800 via-indigo-700 to-indigo-900 rounded-3xl shadow-xl border border-indigo-600"
        >
          {/* Header Section */}
          <motion.h2
            className="text-4xl font-bold text-white mb-8 text-center tracking-wide"
            initial={{ opacity: 0, x: -40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            🔎 Comparison Result
          </motion.h2>

          {/* Similarity Score Section */}
          <div className="mb-8">
            <motion.p
              className="text-2xl text-white mb-4"
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              Similarity Score:{" "}
              <span className="font-bold text-blue-400">
                {(result.similarity_score * 100).toFixed(2)}%
              </span>
            </motion.p>

            <div className="w-full bg-gray-700 h-4 rounded-xl mt-4 overflow-hidden">
              <motion.div
                className="h-4 bg-gradient-to-r from-blue-500 to-blue-400 rounded-xl"
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
                color: "green-400",
                hoverColor: "green-500",
                shadowColor: "#34d39944",
              },
              {
                title: "📌 Unique Policy 1",
                items: result.details.unique_policy1,
                color: "yellow-400",
                hoverColor: "yellow-500",
                shadowColor: "#facc1544",
              },
              {
                title: "📌 Unique Policy 2",
                items: result.details.unique_policy2,
                color: "red-400",
                hoverColor: "red-500",
                shadowColor: "#f8717144",
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
                className="bg-gray-900 p-6 rounded-xl border border-gray-700 hover:bg-gray-800 transition-colors"
              >
                <h3
                  className={`font-semibold mb-4 text-${section.color} text-2xl`}
                >
                  {section.title}
                </h3>
                <ul className="list-disc list-inside text-gray-300">
                  {section.items.length > 0 ? (
                    section.items.map((item, i) => (
                      <motion.li
                        key={i}
                        whileHover={{
                          color: `text-${section.hoverColor}`,
                          scale: 1.08,
                        }}
                        transition={{ type: "spring", stiffness: 300 }}
                      >
                        {item}
                      </motion.li>
                    ))
                  ) : (
                    <li className="text-gray-500 italic">None</li>
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
