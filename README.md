# 🌍 Climate Policy Analysis Agent

> An AI-powered application for analyzing, comparing, and extracting insights from climate-related policy documents using NLP and machine learning.

---

## 📌 Overview

Climate policy documents are often lengthy, complex, and difficult to compare manually.

The **Climate Policy Analysis Agent** is designed to simplify this process by allowing users to upload climate policy documents and automatically analyze their content using **Natural Language Processing (NLP)** and **Machine Learning (ML)** techniques.

The system can identify important policy information, compare two policies, find overlaps and differences, calculate similarity, and generate recommendations for policy improvement.

### 🎯 Main Goal

Transform:

**Unstructured Policy Documents → Structured Insights → Policy Comparison → Recommendations**

---

## ✨ Features

### 📂 Document Upload

Upload climate policy documents in different formats:

- PDF
- Microsoft Word
- Text

The system extracts the content and prepares it for further analysis.

---

### 🧹 Text Preprocessing

Uploaded documents are processed before analysis.

The preprocessing pipeline handles:

- Text extraction
- Cleaning
- Noise removal
- Text normalization
- Input sanitization

This improves the quality of the downstream NLP analysis.

---

### 🧠 NLP-Based Document Analysis

The system analyzes policy documents using NLP techniques.

It can identify:

- Important keywords
- Policy-related information
- Named Entities
- Relevant sections of policy documents
- Structured policy information

Named Entity Recognition (NER) is used to identify important entities within the documents.

---

### 🤝 Policy Comparison

The **Policy Comparator Agent** allows two policy documents to be compared.

The system identifies:

#### ✅ Common Information

Information, words, phrases, or policy areas shared between the two documents.

#### 🔹 Unique to Policy A

Information found in the first policy but not the second.

#### 🔸 Unique to Policy B

Information found in the second policy but not the first.

#### 📈 Similarity Score

A similarity score is generated to provide an overall indication of how closely the two policies are related.

---

### 🎯 Recommendation Engine

The system uses the results of the policy analysis and comparison to generate recommendations for potential policy improvements.

Recommendations can be based on:

- Missing policy areas
- Differences between policies
- Common policy areas
- Extracted policy information
- Comparative analysis

---

## 🏗️ System Architecture

The application follows an end-to-end document analysis workflow:

```text
                    ┌──────────────────────┐
                    │      User Input      │
                    │  PDF / Word / Text   │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Document Upload    │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │ Text Extraction &    │
                    │   Preprocessing      │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │     NLP Analysis     │
                    │ Keywords + NER        │
                    └───────────┬──────────┘
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
             ┌───────────────┐     ┌────────────────┐
             │ Policy        │     │ Policy         │
             │ Analyzer      │     │ Comparator     │
             └───────┬───────┘     └───────┬────────┘
                     │                     │
                     └──────────┬──────────┘
                                ▼
                    ┌──────────────────────┐
                    │ Similarity &         │
                    │ Difference Analysis  │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │ Recommendation       │
                    │ Engine               │
                    └───────────┬──────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Policy Insights    │
                    │ & Recommendations    │
                    └──────────────────────┘
