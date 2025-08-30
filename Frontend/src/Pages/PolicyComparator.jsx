import React, { useState } from "react";
import axios from "axios";
import {
  Container,
  TextField,
  Button,
  Typography,
  Paper,
  Box,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Collapse,
} from "@mui/material";
import { ExpandMore, ExpandLess } from "@mui/icons-material";
import { motion, AnimatePresence } from "framer-motion";

export default function PolicyComparer() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [openSections, setOpenSections] = useState({
    overlap: true,
    unique1: true,
    unique2: true,
  });

  const toggleSection = (section) => {
    setOpenSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const handleCompare = async () => {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/compare_policy", {
        policy1,
        policy2,
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "An error occurred. Please try again.");
    }
    setLoading(false);
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        position: "relative",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        py: 8,
        overflow: "hidden",
      }}
    >
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

      <Container maxWidth="md">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <Paper
            elevation={12}
            sx={{
              p: 6,
              borderRadius: 4,
              background: "rgba(255,255,255,0.95)",
              boxShadow: "0 12px 32px rgba(0,0,0,0.2)",
            }}
          >
            {/* Header */}
            <Typography
              variant="h3"
              align="center"
              gutterBottom
              sx={{
                fontWeight: 700,
                background: "linear-gradient(90deg, #667eea, #764ba2)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Policy Comparator
            </Typography>

            {/* Input Fields */}
            <TextField
              label="Policy 1"
              multiline
              minRows={4}
              fullWidth
              margin="normal"
              value={policy1}
              onChange={(e) => setPolicy1(e.target.value)}
              variant="outlined"
              sx={{ background: "#f7fbfc", borderRadius: 2 }}
            />
            <TextField
              label="Policy 2"
              multiline
              minRows={4}
              fullWidth
              margin="normal"
              value={policy2}
              onChange={(e) => setPolicy2(e.target.value)}
              variant="outlined"
              sx={{ background: "#f7fbfc", borderRadius: 2 }}
            />

            {/* Compare Button */}
            <Box textAlign="center" mt={3}>
              <Button
                variant="contained"
                size="large"
                onClick={handleCompare}
                disabled={!policy1 || !policy2 || loading}
                sx={{
                  px: 5,
                  py: 1.5,
                  borderRadius: 3,
                  fontWeight: 600,
                  fontSize: "1.1rem",
                  background: "linear-gradient(90deg, #667eea, #764ba2)",
                  boxShadow: "0 6px 20px rgba(102,126,234,0.3)",
                }}
              >
                {loading ? <CircularProgress size={26} color="inherit" /> : "Compare"}
              </Button>
            </Box>

            {/* Error Message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  transition={{ duration: 0.4 }}
                >
                  <Typography color="error" mt={3} align="center">
                    {error}
                  </Typography>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Result Section */}
            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 30 }}
                  transition={{ duration: 0.6 }}
                >
                  <Box mt={5}>
                    <Typography
                      variant="h5"
                      align="center"
                      sx={{ fontWeight: 600, color: "#667eea", letterSpacing: 1 }}
                    >
                      Similarity Score:{" "}
                      {(result.similarity_score * 100).toFixed(2)}%
                    </Typography>

                    {/* Progress Bar */}
                    <Box
                      sx={{
                        width: "100%",
                        height: 12,
                        borderRadius: 6,
                        background: "#e0e0e0",
                        overflow: "hidden",
                        mt: 2,
                      }}
                    >
                      <motion.div
                        style={{ height: "100%", borderRadius: 6, background: "#667eea" }}
                        initial={{ width: 0 }}
                        animate={{ width: `${result.similarity_score * 100}%` }}
                        transition={{ duration: 1, type: "spring" }}
                      />
                    </Box>

                    <Divider sx={{ my: 3 }} />

                    {/* Sections: Overlap, Unique1, Unique2 */}
                    {[{
                        key: "overlap",
                        title: "Overlap Words",
                        items: result.details.overlap,
                      },
                      {
                        key: "unique1",
                        title: "Unique to Policy 1",
                        items: result.details.unique_policy1,
                      },
                      {
                        key: "unique2",
                        title: "Unique to Policy 2",
                        items: result.details.unique_policy2,
                      },
                    ].map((section) => (
                      <Box key={section.key} mb={2}>
                        <Button
                          onClick={() => toggleSection(section.key)}
                          endIcon={openSections[section.key] ? <ExpandLess /> : <ExpandMore />}
                          sx={{
                            textTransform: "none",
                            fontWeight: 600,
                            color: "#333",
                            mb: 1,
                          }}
                        >
                          {section.title}
                        </Button>
                        <Collapse in={openSections[section.key]}>
                          <List dense>
                            {section.items.length === 0 && (
                              <ListItem>
                                <ListItemText primary="None" sx={{ fontStyle: "italic" }} />
                              </ListItem>
                            )}
                            {section.items.map((word, idx) => (
                              <ListItem
                                key={idx}
                                sx={{
                                  borderRadius: 1,
                                  "&:hover": { background: "#f0f0f0", transform: "scale(1.02)" },
                                  transition: "all 0.2s",
                                }}
                              >
                                <ListItemText primary={word} />
                              </ListItem>
                            ))}
                          </List>
                        </Collapse>
                      </Box>
                    ))}
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
}
