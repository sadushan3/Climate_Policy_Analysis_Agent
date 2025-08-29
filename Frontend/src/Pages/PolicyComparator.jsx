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
} from "@mui/material";

export default function PolicyComparer() {
  const [policy1, setPolicy1] = useState("");
  const [policy2, setPolicy2] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleCompare = async () => {
    setError("");
    setResult(null);
    try {
      const res = await axios.post("http://localhost:8000/compare_policy", {
        policy1,
        policy2,
      });
      setResult(res.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "An error occurred. Please try again."
      );
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 6 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
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
        />
        <TextField
          label="Policy 2"
          multiline
          minRows={4}
          fullWidth
          margin="normal"
          value={policy2}
          onChange={(e) => setPolicy2(e.target.value)}
        />
        <Box textAlign="center" mt={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleCompare}
            disabled={!policy1 || !policy2}
          >
            Compare
          </Button>
        </Box>
        {error && (
          <Typography color="error" mt={2}>
            {error}
          </Typography>
        )}
        {result && (
          <Box mt={4}>
            <Typography variant="h6">
              Similarity Score: {result.similarity_score.toFixed(3)}
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1">Overlap Words:</Typography>
            <List dense>
              {result.details.overlap.map((word, idx) => (
                <ListItem key={idx}>
                  <ListItemText primary={word} />
                </ListItem>
              ))}
            </List>
            <Typography variant="subtitle1">Unique to Policy 1:</Typography>
            <List dense>
              {result.details.unique_policy1.map((word, idx) => (
                <ListItem key={idx}>
                  <ListItemText primary={word} />
                </ListItem>
              ))}
            </List>
            <Typography variant="subtitle1">Unique to Policy 2:</Typography>
            <List dense>
              {result.details.unique_policy2.map((word, idx) => (
                <ListItem key={idx}>
                  <ListItemText primary={word} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Container>
  );
}