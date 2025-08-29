import React from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function ResultCard({ result }) {
  if (!result) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="result-card"
        initial={{ opacity: 0, y: 50, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 50, scale: 0.95 }}
        transition={{ duration: 0.6, type: "spring" }}
        className="mt-8 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8 rounded-2xl shadow-2xl border border-gray-700"
      >
        <motion.h2
          className="text-2xl md:text-3xl font-extrabold mb-6 text-white tracking-wide"
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          🔎 Comparison Result
        </motion.h2>

        <div className="mb-6">
          <motion.p
            className="text-lg md:text-xl text-gray-200"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            Similarity Score:{" "}
            <span className="font-bold text-blue-400">
              {(result.similarity_score * 100).toFixed(2)}%
            </span>
          </motion.p>

          <div className="w-full bg-gray-700 h-5 rounded-xl mt-3 overflow-hidden">
            <motion.div
              className="h-5 bg-gradient-to-r from-blue-500 to-blue-400 rounded-xl"
              initial={{ width: 0 }}
              animate={{ width: `${result.similarity_score * 100}%` }}
              transition={{ duration: 1, type: "spring" }}
            />
          </div>
        </div>

        <motion.div
          className="grid md:grid-cols-3 gap-6"
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
              className="bg-gray-900 p-4 rounded-xl border border-gray-700 hover:bg-gray-800 transition-colors"
            >
              <h3
                className={`font-semibold mb-3 text-${section.color} text-lg md:text-xl`}
              >
                {section.title}
              </h3>
              <ul className="list-disc list-inside text-gray-300">
                {section.items.length > 0 ? (
                  section.items.map((w, i) => (
                    <motion.li
                      key={i}
                      whileHover={{
                        color: `text-${section.hoverColor}`,
                        scale: 1.08,
                      }}
                      transition={{ type: "spring", stiffness: 300 }}
                    >
                      {w}
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
  );
}
