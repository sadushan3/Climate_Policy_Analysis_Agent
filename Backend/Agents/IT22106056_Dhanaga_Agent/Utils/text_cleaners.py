"""
Text cleaning functions for climate policy documents
"""
import re
from typing import Set, Dict

class TextCleaners:
    """
    Collection of text cleaning methods for climate policy documents
    """
    
    def __init__(self):
        # Climate policy specific acronyms to preserve
        self.climate_acronyms = {
            'UNFCCC', 'IPCC', 'NDC', 'EU', 'UNEP', 'GHG', 'CO2', 'CH4', 'N2O',
            'LULUCF', 'REDD+', 'CDM', 'JI', 'ETS', 'COP', 'CMP', 'SBI', 'SBSTA',
            'NAMA', 'MRV', 'ICA', 'BUR', 'NC', 'AR', 'WG', 'SPM', 'TS', 'FAQ'
        }
    
    def basic_text_cleaning(self, text: str) -> str:
        """
        1. Lowercasing (preserve acronyms)
        2. Whitespace & line break normalization
        3. Punctuation normalization
        """
        # Preserve acronyms before lowercasing
        acronym_placeholders = {}
        for i, acronym in enumerate(self.climate_acronyms):
            placeholder = f"__ACRONYM_{i}__"
            text = re.sub(rf'\b{re.escape(acronym)}\b', placeholder, text)
            acronym_placeholders[placeholder] = acronym
        
        # Convert to lowercase
        text = text.lower()
        
        # Restore acronyms
        for placeholder, acronym in acronym_placeholders.items():
            text = text.replace(placeholder, acronym)
        
        # Normalize whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r'\t', ' ', text)  # Tabs to spaces
        
        # Keep policy-relevant punctuation, remove unnecessary symbols
        text = re.sub(r'[###\*\*\*•▪▫]', '', text)  # Remove bullets and symbols
        
        return text.strip()
    
    def remove_headers_footers(self, text: str) -> str:
        """
        Remove headers, footers, page numbers, and repeated phrases
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Remove page numbers
            if re.match(r'^page\s+\d+(\s+of\s+\d+)?$', line, re.IGNORECASE):
                continue
            
            # Remove line numbers at start
            line = re.sub(r'^\d+\.\s*', '', line)
            
            # Remove common header/footer patterns
            header_footer_patterns = [
                r'^(ministry|department|government).*\d{4}$',
                r'^draft.*\d{4}$',
                r'^confidential.*draft$',
                r'^\d+\s*$',  # Just numbers
                r'^page\s+\d+',
                r'^\d{1,3}\s+of\s+\d{1,3}$'
            ]
            
            skip_line = False
            for pattern in header_footer_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    skip_line = True
                    break
            
            if not skip_line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def clean_special_characters(self, text: str) -> str:
        """
        Clean Unicode artifacts and normalize special characters
        """
        # Remove Unicode artifacts
        text = re.sub(r'[\xa0\u00a0\u2000-\u200f\u2028\u2029]', ' ', text)
        text = re.sub(r'[©®™]', '', text)
        
        # Normalize dashes
        text = re.sub(r'[–—]', '-', text)
        
        # Fix hyphenated words split across lines
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
