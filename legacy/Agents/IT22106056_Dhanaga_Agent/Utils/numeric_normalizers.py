"""
Numeric and date normalization functions for climate policy documents
"""
import re

class NumericNormalizers:
    """
    Collection of numeric and date normalization methods
    """

    def __init__(self):
        # Month mapping for date normalization
        self.month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }

        # Number words mapping (basic)
        self.number_words = {
            'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50',
            'sixty': '60', 'seventy': '70', 'eighty': '80', 'ninety': '90',
            'hundred': '100', 'thousand': '1000', 'million': '1000000',
            'billion': '1000000000'
        }

    def normalize_numeric_and_dates(self, text: str) -> str:
        """
        Main function to normalize all numeric and date formats
        """
        text = self._normalize_percentages(text)
        text = self._normalize_years(text)
        text = self._normalize_dates(text)
        text = self._normalize_currency(text)
        text = self._normalize_emissions_units(text)
        text = self._convert_written_numbers(text)
        return text

    def handle_missing_values(self, text: str) -> str:
        """Handle missing numeric values with placeholders and approximate phrases"""
        # Replace missing percentages with placeholder
        text = re.sub(r'reduce\s+emissions\s+by\s+___?%', 'reduce emissions by MISSING%', text, flags=re.IGNORECASE)

        # Approximate phrases
        text = re.sub(r'around\s+(\d+)%', r'≈\1%', text, flags=re.IGNORECASE)
        text = re.sub(r'less\s+than\s+(\d+)%', r'<\1%', text, flags=re.IGNORECASE)
        text = re.sub(r'more\s+than\s+(\d+)%', r'>\1%', text, flags=re.IGNORECASE)

        # Ranges and missing upper bound
        text = re.sub(r'(\d+)[–-](\d+)%', r'\1-\2%', text)
        text = re.sub(r'(\d+)[–-]___%', r'\1-MISSING%', text)
        return text

    # ---- helpers ----
    def _normalize_percentages(self, text: str) -> str:
        text = re.sub(r'(\d+)\s*%', r'\1%', text)
        text = re.sub(r'(\d+)\s+percent', r'\1%', text, flags=re.IGNORECASE)
        return text

    def _normalize_years(self, text: str) -> str:
        text = re.sub(r'\byear\s+(\d{4})\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\bby\s+the\s+year\s+(\d{4})\b', r'by \1', text, flags=re.IGNORECASE)
        text = re.sub(r"\bin\s+'(\d{2})\b", lambda m: f"in 20{m.group(1)}" if int(m.group(1)) < 50 else f"in 19{m.group(1)}", text)
        return text

    def _normalize_dates(self, text: str) -> str:
        # 31st December 2030 -> 2030-12-31
        pattern1 = r'(\d{1,2})(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})'
        text = re.sub(pattern1, self._replace_date_format1, text, flags=re.IGNORECASE)
        # December 31, 2030 -> 2030-12-31
        pattern2 = r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})'
        text = re.sub(pattern2, self._replace_date_format2, text, flags=re.IGNORECASE)
        # 2030, December -> 2030-12
        pattern3 = r'(\d{4}),?\s+(january|february|march|april|may|june|july|august|september|october|november|december)'
        text = re.sub(pattern3, self._replace_date_format3, text, flags=re.IGNORECASE)
        return text

    def _replace_date_format1(self, m):
        day, _, month, year = m.groups()
        month_num = self.month_map.get(month.lower(), month)
        return f"{year}-{month_num}-{day.zfill(2)}"

    def _replace_date_format2(self, m):
        month, day, year = m.groups()
        month_num = self.month_map.get(month.lower(), month)
        return f"{year}-{month_num}-{day.zfill(2)}"

    def _replace_date_format3(self, m):
        year, month = m.groups()
        month_num = self.month_map.get(month.lower(), month)
        return f"{year}-{month_num}"

    def _normalize_currency(self, text: str) -> str:
        text = re.sub(r'\$(\d+)bn\b', r'\1,000,000,000 USD', text, flags=re.IGNORECASE)
        text = re.sub(r'\$(\d+)m\b', r'\1,000,000 USD', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s+billion\s+USD', r'\1,000,000,000 USD', text, flags=re.IGNORECASE)
        text = re.sub(r'Rs\.?\s*(\d+)\s+million', r'\1,000,000 INR', text, flags=re.IGNORECASE)
        return text

    def _normalize_emissions_units(self, text: str) -> str:
        text = re.sub(r'(\d+)\s*MtCO2e?\b', r'\1 million tonnes CO2e', text, flags=re.IGNORECASE)
        text = re.sub(r'(\d+)\s*GtCO2e?\b', r'\1 billion tonnes CO2e', text, flags=re.IGNORECASE)
        # Energy units normalization (basic)
        text = re.sub(r'\bkWh\b', 'kWh', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMWh\b', 'MWh', text, flags=re.IGNORECASE)
        text = re.sub(r'\bgigatonnes?\b', 'Gt', text, flags=re.IGNORECASE)
        return text

    def _convert_written_numbers(self, text: str) -> str:
        for word, digit in self.number_words.items():
            text = re.sub(rf'\b{word}\b', digit, text, flags=re.IGNORECASE)
        # very basic compound handling
        text = re.sub(r'\b(\d+)-(\d+)\s+million\b', lambda m: str(int(m.group(1)) + int(m.group(2))) + '000000', text)
        text = re.sub(r'\bone\s+hundred\s+and\s+(\d+)\b', lambda m: str(100 + int(m.group(1))), text, flags=re.IGNORECASE)
        return text
