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
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";

export default function PolicyComparer() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
      setError(
        err.response?.data?.detail || "An error occurred. Please try again."
      );
    }
    setLoading(false);
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%)",
        py: 8,
      }}
    >
      <Container maxWidth="sm">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <Paper
            elevation={6}
            sx={{
              p: 5,
              borderRadius: 4,
              background: "rgba(255,255,255,0.95)",
              boxShadow: "0 8px 32px 0 rgba(31, 38, 135, 0.2)",
            }}
          >
            <Typography
              variant="h3"
              align="center"
              gutterBottom
              sx={{
                fontWeight: 700,
                background: "linear-gradient(90deg, #2193b0, #6dd5ed)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Policy Comparator
            </Typography>
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
            <Box textAlign="center" mt={3}>
              <Button
                variant="contained"
                color="primary"
                size="large"
                onClick={handleCompare}
                disabled={!policy1 || !policy2 || loading}
                sx={{
                  px: 5,
                  py: 1.5,
                  borderRadius: 3,
                  fontWeight: 600,
                  fontSize: "1.1rem",
                  background: "linear-gradient(90deg, #2193b0, #6dd5ed)",
                  boxShadow: "0 4px 20px 0 rgba(33,147,176,0.2)",
                }}
              >
                {loading ? <CircularProgress size={26} color="inherit" /> : "Compare"}
              </Button>
            </Box>
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
                      sx={{
                        fontWeight: 600,
                        color: "#2193b0",
                        letterSpacing: 1,
                      }}
                    >
                      Similarity Score: {result.similarity_score.toFixed(3)}
                    </Typography>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Overlap Words:
                    </Typography>
                    <List dense>
                      {result.details.overlap.length === 0 && (
                        <ListItem>
                          <ListItemText primary="No overlap" />
                        </ListItem>
                      )}
                      {result.details.overlap.map((word, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={word} />
                        </ListItem>
                      ))}
                    </List>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Unique to Policy 1:
                    </Typography>
                    <List dense>
                      {result.details.unique_policy1.length === 0 && (
                        <ListItem>
                          <ListItemText primary="None" />
                        </ListItem>
                      )}
                      {result.details.unique_policy1.map((word, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={word} />
                        </ListItem>
                      ))}
                    </List>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      Unique to Policy 2:
                    </Typography>
                    <List dense>
                      {result.details.unique_policy2.length === 0 && (
                        <ListItem>
                          <ListItemText primary="None" />
                        </ListItem>
                      )}
                      {result.details.unique_policy2.map((word, idx) => (
                        <ListItem key={idx}>
                          <ListItemText primary={word} />
                        </ListItem>
                      ))}
                    </List>
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