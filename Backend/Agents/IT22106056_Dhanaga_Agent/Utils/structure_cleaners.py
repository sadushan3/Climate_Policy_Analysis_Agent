"""
Structure-oriented and climate policy specific cleaning functions
"""
import re
from typing import Set, List

class StructureCleaners:
    """
    Collection of structure-oriented and domain-specific cleaning methods
    """
    
    def __init__(self):
        # Climate policy synonyms for standardization
        self.climate_synonyms = {
            r'\bcarbon\s+dioxide\b': 'CO2',
            r'\bmethane\b': 'CH4',
            r'\bnitrous\s+oxide\b': 'N2O',
            r'\bgreenhouse\s+gas(es)?\b': 'GHG',
            r'\bemission\s+reduction(s)?\b': 'mitigation',
            r'\bclimate\s+change\s+adaptation\b': 'adaptation',
            r'\brenewable\s+energy\b': 'renewable energy',
            r'\benergy\s+efficiency\b': 'energy efficiency'
        }
    
    def structure_oriented_cleaning(self, text: str) -> str:
        """
        Main structure-oriented cleaning function
        """
        text = self._remove_table_figure_captions(text)
        text = self._remove_duplicate_sentences(text)
        text = self._fix_sentence_boundaries(text)
        text = self._section_splitting(text)
        return text
    
    def _remove_table_figure_captions(self, text: str) -> str:
        """Remove table and figure captions"""
        # Remove figure/table/chart references
        text = re.sub(r'\b(figure|table|chart|graph)\s+\d+[\.:]\s*[^\n]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(fig|tab)\.\s*\d+[\.:]\s*[^\n]*', '', text, flags=re.IGNORECASE)
        
        # Remove "see figure X" references
        text = re.sub(r'\(see\s+(figure|table|chart)\s+\d+\)', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_duplicate_sentences(self, text: str) -> str:
        """Remove duplicate sentences often caused by OCR or PDF extraction"""
        sentences = re.split(r'[.!?]+', text)
        unique_sentences = []
        seen_sentences = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Ignore very short fragments
                # Normalize for comparison (remove extra spaces, lowercase)
                normalized = re.sub(r'\s+', ' ', sentence.lower())
                if normalized not in seen_sentences:
                    unique_sentences.append(sentence)
                    seen_sentences.add(normalized)
        
        return '. '.join(unique_sentences)
    
    def _fix_sentence_boundaries(self, text: str) -> str:
        """Ensure proper sentence boundaries"""
        # Fix missing spaces after periods
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Fix multiple punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Ensure sentences end with proper punctuation
        text = re.sub(r'([a-zA-Z])\s*\n\s*([A-Z])', r'\1. \2', text)
        
        return text
    
    def _section_splitting(self, text: str) -> str:
        """Detect and organize sections by headings"""
        # Common policy document sections
        section_headers = [
            r'\b(introduction|executive\s+summary)\b',
            r'\b(objectives?|goals?|targets?)\b',
            r'\b(mitigation|adaptation)\b',
            r'\b(implementation|monitoring)\b',
            r'\b(conclusion|summary)\b',
            r'\b(annex|appendix)\b'
        ]
        
        # Add section markers for better organization
        for header_pattern in section_headers:
            text = re.sub(f'^({header_pattern})', r'\n=== \1 ===\n', text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text
    
    def climate_policy_specific_cleaning(self, text: str) -> str:
        """
        Climate policy domain-specific cleaning
        """
        text = self._remove_annexes_references(text)
        text = self._standardize_climate_terms(text)
        text = self._remove_legal_boilerplate(text)
        text = self._entity_tagging_prep(text)
        return text
    
    def _remove_annexes_references(self, text: str) -> str:
        """Remove annexes and references sections"""
        # Remove annex sections
        text = re.sub(r'\bannex\s+[a-z]\b.*?(?=\n\n|\Z)', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove references sections
        text = re.sub(r'\b(references?|bibliography)\s*\n.*?(?=\n\n|\Z)', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove footnote references
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\(\d+\)', '', text)
        
        return text
    
    def _standardize_climate_terms(self, text: str) -> str:
        """Standardize climate policy terminology"""
        for pattern, replacement in self.climate_synonyms.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Standardize common policy phrases
        text = re.sub(r'\bnational(ly)?\s+determined\s+contribution(s)?\b', 'NDC', text, flags=re.IGNORECASE)
        text = re.sub(r'\bparis\s+agreement\b', 'Paris Agreement', text, flags=re.IGNORECASE)
        text = re.sub(r'\bkyoto\s+protocol\b', 'Kyoto Protocol', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_legal_boilerplate(self, text: str) -> str:
        """Remove common legal boilerplate text"""
        boilerplate_patterns = [
            r'\bhereby\s+acknowledge(s)?\b',
            r'\bthereof\s+and\s+thereto\b',
            r'\bwhereas\b.*?(?=\n)',
            r'\bnow\s+therefore\b',
            r'\bin\s+witness\s+whereof\b'
        ]
        
        for pattern in boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _entity_tagging_prep(self, text: str) -> str:
        """Prepare text for Named Entity Recognition"""
        # Ensure proper capitalization for countries and organizations
        countries = ['united states', 'european union', 'china', 'india', 'brazil', 'russia', 'japan']
        for country in countries:
            text = re.sub(rf'\b{country}\b', country.title(), text, flags=re.IGNORECASE)
        
        # Ensure proper formatting for dates and numbers
        text = re.sub(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', r'\3-\2-\1', text)  # US date format to ISO
        
        return text
    
    def final_cleanup(self, text: str) -> str:
        """Final cleanup and normalization"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Ensure proper sentence spacing
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove empty lines at the beginning and end
        text = re.sub(r'^\n+', '', text)
        text = re.sub(r'\n+$', '', text)
        
        return text
    
    def remove_repeated_paragraphs(self, text: str) -> str:
        """Remove repeated paragraphs often found in policy documents"""
        paragraphs = text.split('\n\n')
        unique_paragraphs = []
        seen_paragraphs = set()
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Normalize for comparison
                normalized = re.sub(r'\s+', ' ', paragraph.lower())
                if normalized not in seen_paragraphs and len(normalized) > 20:
                    unique_paragraphs.append(paragraph)
                    seen_paragraphs.add(normalized)
        
        return '\n\n'.join(unique_paragraphs)
