import React, { useState } from 'react';
import { Box, Container, TextField, Button, Typography, Paper, CircularProgress } from '@mui/material';

// We'll use a simple state-based router since we're in a single file
function PolicyResult({ result, onBack }) {
  const resultText = JSON.stringify(result, null, 2);
  
  return (
    <Container
      maxWidth="sm"
      sx={{
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
      }}
    >
      <Paper elevation={12} sx={{
        p: 6,
        borderRadius: 4,
        boxShadow: '0 12px 32px rgba(0,0,0,0.2)',
        width: '100%',
        maxWidth: '600px',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
      }}>
        <Typography variant="h4" align="center" gutterBottom>
          Comparison Result
        </Typography>
        <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(0,0,0,0.05)', borderRadius: 2, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
          {resultText}
        </Box>
        <Box textAlign="center" mt={3}>
          <Button variant="outlined" size="large" onClick={onBack}>
            Go Back
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}


function PolicyComparator({ onCompareSuccess }) {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    setError("");
    setLoading(true);
    try {
      // Since we don't have a backend, we'll simulate the API call.
      // In a real app, you would replace this with your axios call.
      const simulatedResult = {
        summary: "The first policy is more comprehensive regarding environmental regulations, while the second policy is stronger on data privacy protection.",
        common_points: ["Risk assessment", "Compliance with local laws"],
        differences: [
          "Policy 1 includes clauses for carbon footprint reporting, which Policy 2 lacks.",
          "Policy 2 has a detailed section on data breach notification, which is not present in Policy 1."
        ]
      };
      
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate network delay
      onCompareSuccess(simulatedResult);
    } catch (err) {
      setError("An error occurred. Please try again.");
    }
    setLoading(false);
  };

  return (
    <Container
      maxWidth="sm"
      sx={{
        position: "relative",
        zIndex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
      }}
    >
      <Paper
        elevation={12}
        sx={{
          p: 6,
          borderRadius: 4,
          boxShadow: "0 12px 32px rgba(0,0,0,0.2)",
          width: "100%",
          maxWidth: "600px",
          backgroundColor: "rgba(255, 255, 255, 0.8)",
        }}
      >
        <Typography variant="h3" align="center" gutterBottom>
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
        />

        <Box textAlign="center" mt={3}>
          <Button
            variant="contained"
            size="large"
            onClick={handleCompare}
            disabled={!policy1 || !policy2 || loading}
          >
            {loading ? <CircularProgress size={26} color="inherit" /> : "Compare"}
          </Button>
        </Box>

        {error && <Typography color="error" mt={3} align="center">{error}</Typography>}
      </Paper>
    </Container>
  );
}

export default function App() {
  const [result, setResult] = useState(null);

  const handleCompareSuccess = (data) => {
    setResult(data);
  };

  return (
    <Box sx={{ minHeight: "100vh", position: "relative" }}>
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
        <source src="" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Centered Content */}
      {!result ? (
        <PolicyComparator onCompareSuccess={handleCompareSuccess} />
      ) : (
        <PolicyResult result={result} onBack={() => setResult(null)} />
      )}
    </Box>
  );
}
