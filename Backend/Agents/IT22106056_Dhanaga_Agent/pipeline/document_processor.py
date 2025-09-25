# Backend/Agents/IT22106056_Dhanaga_Agent/pipeline/document_processor.py

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
import hashlib
import re
from collections import OrderedDict
from typing import Optional, Tuple

from ..models.document import (
    Document,
    DocumentMetadata,
    DocumentSection,
    DocumentProcessingOptions,
)

logger = logging.getLogger(__name__)


class DocumentProcessingPipeline:
    """
    Pipeline for processing raw policy documents into structured JSON format.
    Uses _SimpleDocumentCleaner for comprehensive text cleaning and preprocessing.
    """

    def __init__(self, upload_dir: str, output_dir: str):
        """
        Initialize the pipeline with input and output directories.

        Args:
            upload_dir: Directory where raw documents are uploaded
            output_dir: Directory to store processed JSON files
        """
        self.upload_dir = Path(upload_dir)
        self.output_dir = Path(output_dir)
        self.document_cleaner = _SimpleDocumentCleaner()

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_document(
        self,
        file_path: Path,
        options: Optional[DocumentProcessingOptions] = None,
    ) -> Dict[str, Any]:
        """
        Process a single document through the pipeline.

        Args:
            file_path: Path to the document file
            options: Optional processing options

        Returns:
            Dictionary containing the processed document data
        """
        if options is None:
            options = DocumentProcessingOptions()

        try:
            # Clean and process the document
            cleaned_data = self.document_cleaner.clean_document(file_path)

            # Generate a unique document ID
            doc_id = self._generate_document_id(file_path, cleaned_data)

            # Get metadata from cleaned data
            metadata = cleaned_data.get("metadata", {})
            metadata.update(
                {
                    "title": file_path.stem,
                    "file_type": file_path.suffix.lstrip(".").lower() or "pdf",
                }
            )

            # Ensure section extraction is enabled
            options.extract_sections = True
            sections = self._process_sections(cleaned_data.get("sections", {}), options)

            # No keywords extraction in this version
            keywords: List[str] = []

            # Build the document data structure
            document_data = {
                "id": doc_id,
                "file_name": file_path.name,
                "file_size": os.path.getsize(file_path),
                "file_type": metadata.get("file_type", "pdf"),
                "text": cleaned_data.get("text", ""),
                "sections": [
                    {
                        "title": title if title != "content" else "Document Content",
                        "content": content,
                        "start_line": 0,
                        "end_line": len(content.split("\n")),
                    }
                    for title, content in sections.items()
                ]
                if sections
                else [
                    {
                        "title": "Document Content",
                        "content": cleaned_data.get("text", ""),
                        "start_line": 0,
                        "end_line": len(cleaned_data.get("text", "").split("\n")),
                    }
                ],
                "metadata": metadata,
                "keywords": keywords,
                "processing_date": datetime.utcnow().isoformat(),
                "language": cleaned_data.get("language"),
            }

            return document_data

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise

    def _generate_document_id(self, file_path: Path, cleaned_data: Dict[str, Any]) -> str:
        """
        Generate a stable ID using filename, size, and a slice of cleaned text.
        """
        content = f"{file_path.name}{file_path.stat().st_size}"
        txt = cleaned_data.get("text", "")
        if txt:
            content += txt[:1000]
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _process_sections(
        self, sections: Dict[str, str], options: DocumentProcessingOptions
    ) -> Dict[str, str]:
        """
        Normalize section titles and drop empties.
        """
        if not options.extract_sections:
            return {"Document Content": "\n\n".join(sections.values())}
        if not sections:
            return {"Document Content": ""}
        out: Dict[str, str] = {}
        for title, content in sections.items():
            t = (title or "").strip() or "Document Content"
            c = (content or "").strip()
            if c:
                out[t] = c
        return out or {"Document Content": ""}

    def save_as_json(self, document_data: Dict[str, Any]) -> Path:
        """
        Save processed document as pretty JSON in the output directory.
        """
        doc_id = document_data.get("id", "document")
        output_file = self.output_dir / f"{doc_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(document_data, f, indent=2, ensure_ascii=False)
        return output_file

    def process_directory(self, input_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Process all PDFs in the directory and save outputs to JSON.
        """
        input_dir = Path(input_dir) if input_dir else self.upload_dir
        processed: List[Dict[str, Any]] = []
        for pdf in input_dir.glob("*.pdf"):
            try:
                data = self.process_document(pdf)
                self.save_as_json(data)
                processed.append(data)
            except Exception as e:
                logger.error(f"Failed to process {pdf}: {e}")
        return processed


class _SimpleDocumentCleaner:
    """
    Compact, modular cleaner with PDF-only extraction and core normalization.
    """

    ACRONYMS = {"UNFCCC", "IPCC", "NDC", "EU"}

    # ---------------- Extraction ---------------- #
    def _extract_pdf(self, file_path: Path) -> Tuple[str, Optional[int]]:
        """
        Extract text from PDF and return (text, page_count).
        Primary: PyMuPDF (fitz). Fallback: pdfplumber.
        """
        try:
            import fitz  # PyMuPDF

            parts: List[str] = []
            page_count = 0
            with fitz.open(file_path) as doc:
                page_count = len(doc)
                for page in doc:
                    parts.append(page.get_text("text"))
            return "\n".join(parts), page_count
        except Exception:
            # Fallback: pdfplumber
            try:
                import pdfplumber

                parts: List[str] = []
                page_count = 0
                with pdfplumber.open(file_path) as pdf:
                   page_count = len(pdf.pages)
                   for page in pdf.pages:
                      parts.append(page.extract_text() or "")
                return "\n".join(parts), page_count
            except Exception as e:
                raise RuntimeError(f"PDF extraction failed: {e}")
                      
    def _extract_docx(self, file_path: Path) -> str:
        """
        Extract text from DOCX using python-docx.
        Pages concept does not exist for DOCX, so caller should set page_count=None.
        """

        try:
            from docx import Document as DocxDocument  # python-docx
            doc = DocxDocument(file_path)
            # Join non-empty paragraph texts
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception as e:
            raise RuntimeError(f"DOCX extraction failed: {e}")






    
    # ---------------- Cleaning ---------------- #
    def _normalize_unicode(self, t: str) -> str:
        # Remove common artifacts and normalize dashes
        t = t.replace("\xa0", " ")
        t = t.replace("–", "-").replace("—", "-")
        t = re.sub(r"[©®]", "", t)
        return t

    def _remove_headers_footers(self, t: str) -> str:
        out: List[str] = []
        for ln in t.splitlines():
            s = ln.strip()
            if not s:
                continue
            # Remove "Page x of y", "Page x", standalone numbers, common disclaimers
            if re.search(r"^page\s+\d+(\s+of\s+\d+)?$", s, re.I):
                continue
            if re.match(r"^(confidential draft|draft|annex|appendix)\b", s, re.I):
                continue
            if re.match(r"^\d+$", s):
                continue
            out.append(s)
        return "\n".join(out)

    def _normalize_punct(self, t: str) -> str:
        # Drop bullets and hashes, keep policy punctuation: %, -, /, :
        t = re.sub(r"[•●▪◆◇¤§]+", " ", t)
        t = re.sub(r"[#*_]{2,}", " ", t)
        t = re.sub(r"\s*([%\-/:])\s*", r" \1 ", t)
        return re.sub(r"\s{2,}", " ", t).strip()

    def _lowercase_preserve_acronyms(self, t: str) -> str:
        # Lowercase tokens except climate acronyms
        toks = re.split(r"(\W+)", t)
        return "".join(
            tok.upper() if tok.isalpha() and tok.upper() in self.ACRONYMS else (tok.lower() if tok.isalpha() else tok)
            for tok in toks
        )

    def _whitespace(self, t: str) -> str:
        # Fix hyphenated line breaks and normalize whitespace
        t = re.sub(r"([A-Za-z])-\s*\n\s*([A-Za-z])", r"\1 \2", t)
        t = t.replace("\t", " ")
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"\s*\n\s*", "\n", t)
        return t.strip()

    def _sentences(self, t: str) -> List[str]:
        # Simple sentence segmentation
        parts = re.split(r"(?<=[.!?])\s+", t)
        return [p.strip() for p in parts if p.strip()]

    def _dedup(self, sents: List[str]) -> List[str]:
        # Remove duplicate sentences while preserving order
        seen = OrderedDict()
        for s in sents:
            seen.setdefault(s, None)
        return list(seen.keys())

    def _sections(self, t: str) -> Dict[str, str]:
        # Split by key headings if present; otherwise single section
        heads = ["introduction", "objectives", "mitigation", "adaptation", "implementation", "conclusion"]
        pat = re.compile(rf"^(?:{'|'.join(heads)})\b.*$", re.I | re.M)
        ms = list(pat.finditer(t))
        if not ms:
            return {"Document Content": t.strip()}
        out: Dict[str, str] = {}
        for i, m in enumerate(ms):
            start = m.end()
            end = ms[i + 1].start() if i + 1 < len(ms) else len(t)
            out[m.group(0).strip()] = t[start:end].strip()
        return out

    def _numeric_date_norm(self, t: str) -> str:
        # Lightweight numeric/date normalization scaffolding
        t = re.sub(r"\b(\d+)\s*%\b", r"\1%", t)  # 20 % -> 20%
        t = re.sub(r"\b(?:year\s+)(\d{4})\b", r"\1", t, flags=re.I)  # "Year 2030" -> "2030"
        return t

    def _forward_to_analyzer(self, payload: Dict[str, Any]) -> None:
        """
        Send cleaned payload to Document Analyzer Agent if configured.

        Requires env:
            ANALYZER_URL (required to send)
            ANALYZER_API_KEY (optional)
        """
        url = os.getenv("ANALYZER_URL")
        if not url:
            logger.warning("ANALYZER_URL not set; skipping analyzer forwarding.")
            return

        try:
            import requests  # type: ignore
        except Exception:
            logger.warning("requests not installed; cannot forward to analyzer. Add 'requests' to requirements.")
            return

        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("ANALYZER_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code >= 400:
                logger.warning(f"Analyzer responded with status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Failed to forward to analyzer: {e}")
        return

    # ---------------- Public API ---------------- #
    def clean_document(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract, clean, and structure the document. PDF and DOC.
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            # Extract PDF text and pages
            raw, page_count = self._extract_pdf(file_path)
        elif suffix == ".docx":
            # Extract DOCX text; no pages
            raw = self._extract_docx(file_path)
            page_count = None
        else:
            raise ValueError("Only PDF or DOCX is supported.")

        # Cleaning pipeline
        t = self._normalize_unicode(raw)
        t = self._remove_headers_footers(t)
        t = self._normalize_punct(t)
        t = self._lowercase_preserve_acronyms(t)
        t = self._numeric_date_norm(t)
        t = self._whitespace(t)

        # Sentences and de-duplication
        sents = self._sentences(t)
        sents = self._dedup(sents)
        cleaned = "\n".join(sents)

        # Sections
        sections = self._sections(cleaned)

        # Minimal metadata
        meta = {
            "file_type": file_path.suffix.lstrip(".") or "pdf",
            "page_count": page_count,
        }

        # Forward to analyzer (non-blocking)
        try:
            self._forward_to_analyzer({"text": cleaned, "sections": sections, "metadata": meta})
        except Exception:
            pass

        # Detect language (best-effort)
        lang = None
        try:
            from langdetect import detect  # type: ignore
            sample = cleaned[:2000] if cleaned else raw[:2000]
            if sample and sample.strip():
               lang = detect(sample)
        except Exception:
            lang = None

        return {"text": cleaned, "sections": sections, "metadata": meta, "language": lang}