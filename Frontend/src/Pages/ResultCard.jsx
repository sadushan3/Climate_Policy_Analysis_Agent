import React from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function ResultCard({ result }) {
  if (!result) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="result-card"
        initial={{ opacity: 0, y: 40, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 40, scale: 0.95 }}
        transition={{ duration: 0.6, type: "spring" }}
        className="mt-8 bg-gray-800 p-6 rounded-xl shadow-lg"
      >
        <motion.h2
          className="text-xl font-bold mb-4"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          🔎 Comparison Result
        </motion.h2>
        <div className="mb-4">
          <motion.p
            className="text-lg"
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            Similarity Score:{" "}
            <span className="font-bold text-blue-400">
              {(result.similarity_score * 100).toFixed(2)}%
            </span>
          </motion.p>
          <div className="w-full bg-gray-700 h-4 rounded-lg mt-2 overflow-hidden">
            <motion.div
              className="h-4 bg-blue-500 rounded-lg"
              initial={{ width: 0 }}
              animate={{ width: `${result.similarity_score * 100}%` }}
              transition={{ duration: 0.8, type: "spring" }}
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
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0 },
            }}
            whileHover={{ scale: 1.03, boxShadow: "0 0 16px #34d39944" }}
          >
            <h3 className="font-semibold text-green-400 mb-2">✅ Overlap</h3>
            <ul className="list-disc list-inside text-gray-300">
              {result.details.overlap.length > 0 ? (
                result.details.overlap.map((w, i) => (
                  <motion.li
                    key={i}
                    whileHover={{ color: "#34d399", scale: 1.08 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    {w}
                  </motion.li>
                ))
              ) : (
                <li className="text-gray-500">None</li>
              )}
            </ul>
          </motion.div>
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0 },
            }}
            whileHover={{ scale: 1.03, boxShadow: "0 0 16px #facc1544" }}
          >
            <h3 className="font-semibold text-yellow-400 mb-2">
              📌 Unique Policy 1
            </h3>
            <ul className="list-disc list-inside text-gray-300">
              {result.details.unique_policy1.length > 0 ? (
                result.details.unique_policy1.map((w, i) => (
                  <motion.li
                    key={i}
                    whileHover={{ color: "#facc15", scale: 1.08 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    {w}
                  </motion.li>
                ))
              ) : (
                <li className="text-gray-500">None</li>
              )}
            </ul>
          </motion.div>
          <motion.div
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0 },
            }}
            whileHover={{ scale: 1.03, boxShadow: "0 0 16px #f8717144" }}
          >
            <h3 className="font-semibold text-red-400 mb-2">
              📌 Unique Policy 2
            </h3>
            <ul className="list-disc list-inside text-gray-300">
              {result.details.unique_policy2.length > 0 ? (
                result.details.unique_policy2.map((w, i) => (
                  <motion.li
                    key={i}
                    whileHover={{ color: "#f87171", scale: 1.08 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    {w}
                  </motion.li>
                ))
              ) : (
                <li className="text-gray-500">None</li>
              )}
            </ul>
          </motion.div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}