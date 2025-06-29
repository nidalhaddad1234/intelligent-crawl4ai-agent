#!/usr/bin/env python3
"""
Data Normalizer
Cleans and normalizes extracted data for consistent database storage
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import urlparse, urljoin
import json

logger = logging.getLogger("data_normalizer")

class DataNormalizer:
    """Handles cleaning and normalization of extracted web scraping data"""
    
    def __init__(self):
        # Phone number cleaning patterns
        self.phone_patterns = {
            'clean': re.compile(r'[^\d\+\(\)\-\s]'),
            'format': re.compile(r'[\(\)\-\s]'),
            'international': re.compile(r'^\+\d{1,3}'),
            'us_format': re.compile(r'^(\d{3})(\d{3})(\d{4})$')
        }
        
        # Email validation pattern
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # URL patterns
        self.url_patterns = {
            'protocol': re.compile(r'^https?://'),
            'domain': re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
        }
        
        # Common text cleaning patterns
        self.text_patterns = {
            'whitespace': re.compile(r'\s+'),
            'special_chars': re.compile(r'[^\w\s\-\.\,\;\:\!\?\(\)]'),
            'html_entities': re.compile(r'&[a-zA-Z0-9#]+;'),
            'quotes': re.compile(r'[""''`]')
        }
        
        # Price patterns
        self.price_patterns = {
            'currency': re.compile(r'[\$€£¥₹¢]'),
            'number': re.compile(r'[\d,]+\.?\d*'),
            'range': re.compile(r'([\d,]+\.?\d*)\s*[-–—to]\s*([\d,]+\.?\d*)')
        }
    
    def normalize_extracted_data(self, data: Dict[str, Any], purpose: str = None, 
                                url: str = None) -> Dict[str, Any]:
        """
        Main function to normalize extracted data
        
        Args:
            data: Raw extracted data
            purpose: Extraction purpose for context-aware normalization
            url: Source URL for relative link resolution
            
        Returns:
            Normalized data dictionary
        """
        
        if not isinstance(data, dict):
            return {'content': self.normalize_text(str(data))}
        
        normalized = {}
        
        for key, value in data.items():
            normalized_key = self.normalize_field_name(key)
            normalized_value = self.normalize_field_value(normalized_key, value, purpose, url)
            
            if normalized_value is not None:
                normalized[normalized_key] = normalized_value
        
        # Purpose-specific post-processing
        if purpose:
            normalized = self._apply_purpose_specific_normalization(normalized, purpose)
        
        return normalized
    
    def normalize_field_name(self, field_name: str) -> str:
        """
        Normalize field names for consistent database storage
        
        Args:
            field_name: Original field name
            
        Returns:
            Normalized field name
        """
        
        if not isinstance(field_name, str):
            field_name = str(field_name)
        
        # Convert to lowercase
        normalized = field_name.lower().strip()
        
        # Replace spaces and special characters with underscores
        normalized = re.sub(r'[^\w]', '_', normalized)
        
        # Remove consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Handle empty or very short names
        if not normalized or len(normalized) < 2:
            normalized = f"field_{abs(hash(field_name)) % 1000}"
        
        # Standardize common field name variations
        field_mappings = {
            'company_name': ['business_name', 'org_name', 'organization_name', 'firm_name'],
            'phone_number': ['phone', 'telephone', 'tel', 'mobile', 'cell'],
            'email_address': ['email', 'e_mail', 'mail'],
            'web_site': ['website', 'url', 'homepage', 'site'],
            'street_address': ['address', 'location', 'addr'],
            'postal_code': ['zip_code', 'zip', 'postcode'],
            'description': ['desc', 'summary', 'about', 'bio'],
            'rating_score': ['rating', 'score', 'stars', 'review_score'],
            'price_amount': ['price', 'cost', 'amount', 'fee']
        }
        
        for standard_name, variations in field_mappings.items():
            if normalized in variations:
                return standard_name
        
        return normalized
    
    def normalize_field_value(self, field_name: str, value: Any, purpose: str = None, 
                            url: str = None) -> Any:
        """
        Normalize field value based on field name and detected type
        
        Args:
            field_name: Normalized field name
            value: Raw field value
            purpose: Extraction purpose
            url: Source URL for context
            
        Returns:
            Normalized value
        """
        
        if value is None or value == '':
            return None
        
        # Handle lists and nested data
        if isinstance(value, list):
            return self.normalize_list_value(field_name, value, purpose, url)
        elif isinstance(value, dict):
            return self.normalize_dict_value(value, purpose, url)
        
        # Convert to string for processing
        str_value = str(value).strip()
        
        if not str_value:
            return None
        
        # Field-specific normalization
        if any(keyword in field_name for keyword in ['email', 'mail']):
            return self.normalize_email(str_value)
        
        elif any(keyword in field_name for keyword in ['phone', 'tel', 'mobile']):
            return self.normalize_phone(str_value)
        
        elif any(keyword in field_name for keyword in ['url', 'website', 'link']):
            return self.normalize_url(str_value, url)
        
        elif any(keyword in field_name for keyword in ['price', 'cost', 'amount']):
            return self.normalize_price(str_value)
        
        elif any(keyword in field_name for keyword in ['rating', 'score', 'stars']):
            return self.normalize_rating(str_value)
        
        elif any(keyword in field_name for keyword in ['date', 'time']):
            return self.normalize_date(str_value)
        
        else:
            return self.normalize_text(str_value)
    
    def normalize_email(self, email: str) -> Optional[str]:
        """Normalize and validate email addresses"""
        
        email = email.lower().strip()
        
        # Remove common prefixes
        email = re.sub(r'^(email:|e-mail:|mail:)\s*', '', email)
        
        # Extract email from text
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email)
        if email_match:
            email = email_match.group()
        
        # Validate format
        if self.email_pattern.match(email):
            return email
        
        return None
    
    def normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone numbers to consistent format"""
        
        # Remove common prefixes
        phone = re.sub(r'^(phone:|tel:|call:)\s*', '', phone, flags=re.IGNORECASE)
        
        # Clean non-numeric characters except important ones
        cleaned = self.phone_patterns['clean'].sub('', phone)
        
        # Remove spaces, dashes, parentheses for digit extraction
        digits_only = re.sub(r'[^\d]', '', cleaned)
        
        if not digits_only:
            return None
        
        # Handle different formats
        if len(digits_only) == 10:
            # US format: (XXX) XXX-XXXX
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # US format with country code
            return f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        elif len(digits_only) > 10:
            # International format
            return f"+{digits_only}"
        elif len(digits_only) >= 7:
            # Local format
            return digits_only
        
        return None
    
    def normalize_url(self, url: str, base_url: str = None) -> Optional[str]:
        """Normalize URLs and resolve relative links"""
        
        url = url.strip()
        
        # Remove common prefixes
        url = re.sub(r'^(url:|link:|website:)\s*', '', url, flags=re.IGNORECASE)
        
        # Handle relative URLs
        if not url.startswith(('http://', 'https://')):
            if base_url:
                try:
                    url = urljoin(base_url, url)
                except:
                    pass
            else:
                # Add protocol if missing
                if self.url_patterns['domain'].match(url):
                    url = f"https://{url}"
        
        # Basic URL validation
        try:
            parsed = urlparse(url)
            if parsed.netloc and parsed.scheme in ['http', 'https']:
                # Normalize the URL
                normalized_url = f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path}"
                if parsed.query:
                    normalized_url += f"?{parsed.query}"
                return normalized_url
        except:
            pass
        
        return None
    
    def normalize_price(self, price: str) -> Optional[Dict[str, Any]]:
        """Normalize price information"""
        
        # Check for price ranges
        range_match = self.price_patterns['range'].search(price)
        if range_match:
            min_price = self._extract_numeric_price(range_match.group(1))
            max_price = self._extract_numeric_price(range_match.group(2))
            
            if min_price is not None and max_price is not None:
                return {
                    'type': 'range',
                    'min': min_price,
                    'max': max_price,
                    'currency': self._extract_currency(price),
                    'original': price
                }
        
        # Single price
        numeric_price = self._extract_numeric_price(price)
        if numeric_price is not None:
            return {
                'type': 'single',
                'amount': numeric_price,
                'currency': self._extract_currency(price),
                'original': price
            }
        
        return None
    
    def _extract_numeric_price(self, price_str: str) -> Optional[float]:
        """Extract numeric value from price string"""
        
        # Remove currency symbols
        cleaned = self.price_patterns['currency'].sub('', price_str)
        
        # Extract number
        number_match = self.price_patterns['number'].search(cleaned)
        if number_match:
            try:
                # Remove commas and convert to float
                number_str = number_match.group().replace(',', '')
                return float(number_str)
            except ValueError:
                pass
        
        return None
    
    def _extract_currency(self, price_str: str) -> str:
        """Extract currency symbol from price string"""
        
        currency_map = {
            '$': 'USD',
            '€': 'EUR', 
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR',
            '¢': 'USD'
        }
        
        for symbol, code in currency_map.items():
            if symbol in price_str:
                return code
        
        return 'USD'  # Default
    
    def normalize_rating(self, rating: str) -> Optional[Dict[str, Any]]:
        """Normalize rating/score information"""
        
        # Common rating patterns
        patterns = [
            r'([\d\.]+)\s*[/⭐★]\s*([\d\.]+)',  # 4.5/5, 4.5⭐5
            r'([\d\.]+)\s*out\s*of\s*([\d\.]+)',  # 4.5 out of 5
            r'([\d\.]+)\s*stars?',  # 4.5 stars
            r'([\d\.]+)',  # Just a number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, rating, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:
                        score = float(match.group(1))
                        max_score = float(match.group(2))
                    else:
                        score = float(match.group(1))
                        max_score = 5.0  # Default max
                    
                    return {
                        'score': score,
                        'max_score': max_score,
                        'normalized_score': score / max_score,  # 0-1 scale
                        'original': rating
                    }
                except ValueError:
                    continue
        
        return None
    
    def normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date strings to ISO format"""
        
        # Common date patterns
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # DD Month YYYY
        ]
        
        # Try to parse common formats
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    
                    # Handle different formats
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD
                            year, month, day = groups
                        else:  # MM/DD/YYYY or DD-MM-YYYY
                            month, day, year = groups
                        
                        # Create ISO date
                        date_obj = datetime(int(year), int(month), int(day))
                        return date_obj.isoformat()[:10]  # YYYY-MM-DD
                        
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def normalize_text(self, text: str) -> str:
        """Normalize text content"""
        
        if not isinstance(text, str):
            text = str(text)
        
        # Clean HTML entities
        text = self.text_patterns['html_entities'].sub(' ', text)
        
        # Normalize quotes
        text = self.text_patterns['quotes'].sub('"', text)
        
        # Clean excessive whitespace
        text = self.text_patterns['whitespace'].sub(' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text if text else None
    
    def normalize_list_value(self, field_name: str, value_list: List[Any], 
                           purpose: str = None, url: str = None) -> List[Any]:
        """Normalize list values"""
        
        normalized_list = []
        
        for item in value_list:
            if isinstance(item, dict):
                normalized_item = self.normalize_dict_value(item, purpose, url)
            else:
                normalized_item = self.normalize_field_value(field_name, item, purpose, url)
            
            if normalized_item is not None:
                normalized_list.append(normalized_item)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_list = []
        
        for item in normalized_list:
            item_str = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
            if item_str not in seen:
                seen.add(item_str)
                unique_list.append(item)
        
        return unique_list
    
    def normalize_dict_value(self, value_dict: Dict[str, Any], purpose: str = None, 
                           url: str = None) -> Dict[str, Any]:
        """Normalize dictionary values recursively"""
        
        normalized_dict = {}
        
        for key, value in value_dict.items():
            normalized_key = self.normalize_field_name(key)
            normalized_value = self.normalize_field_value(normalized_key, value, purpose, url)
            
            if normalized_value is not None:
                normalized_dict[normalized_key] = normalized_value
        
        return normalized_dict
    
    def _apply_purpose_specific_normalization(self, data: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Apply purpose-specific normalization rules"""
        
        if purpose == 'company_info':
            # Ensure company name is properly formatted
            if 'company_name' in data:
                data['company_name'] = self._normalize_company_name(data['company_name'])
        
        elif purpose == 'contact_discovery':
            # Group contact information
            contacts = {}
            
            for key, value in data.items():
                if 'email' in key:
                    if 'emails' not in contacts:
                        contacts['emails'] = []
                    if isinstance(value, list):
                        contacts['emails'].extend(value)
                    else:
                        contacts['emails'].append(value)
                        
                elif 'phone' in key:
                    if 'phones' not in contacts:
                        contacts['phones'] = []
                    if isinstance(value, list):
                        contacts['phones'].extend(value)
                    else:
                        contacts['phones'].append(value)
            
            # Merge grouped contacts back
            data.update(contacts)
        
        elif purpose == 'product_data':
            # Standardize product information
            if 'product_name' in data and isinstance(data['product_name'], str):
                data['product_name'] = data['product_name'].title()
        
        return data
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company names"""
        
        if not isinstance(name, str):
            return str(name)
        
        # Remove common suffixes for normalization
        suffixes = ['inc', 'inc.', 'corp', 'corp.', 'llc', 'ltd', 'ltd.', 'co', 'co.']
        
        name = name.strip()
        name_lower = name.lower()
        
        # Don't remove suffix if it's part of the actual name
        for suffix in suffixes:
            if name_lower.endswith(f' {suffix}'):
                # Keep the suffix but normalize it
                base_name = name[:-len(suffix)-1].strip()
                normalized_suffix = suffix.upper() if suffix.endswith('.') else suffix.upper() + '.'
                return f"{base_name} {normalized_suffix}"
        
        return name
    
    def calculate_data_quality_score(self, original_data: Dict[str, Any], 
                                   normalized_data: Dict[str, Any]) -> float:
        """Calculate data quality score based on normalization results"""
        
        if not original_data:
            return 0.0
        
        total_fields = len(original_data)
        quality_score = 0.0
        
        for key in original_data:
            normalized_key = self.normalize_field_name(key)
            
            # Check if field was preserved and improved
            if normalized_key in normalized_data:
                quality_score += 1.0
                
                # Bonus for successful normalization
                original_value = original_data[key]
                normalized_value = normalized_data[normalized_key]
                
                if self._is_improvement(original_value, normalized_value):
                    quality_score += 0.5
        
        return min(quality_score / total_fields, 1.0)
    
    def _is_improvement(self, original: Any, normalized: Any) -> bool:
        """Check if normalized value is an improvement over original"""
        
        if original == normalized:
            return False
        
        # String improvements
        if isinstance(original, str) and isinstance(normalized, str):
            return len(normalized.strip()) > len(original.strip())
        
        # Type improvements (string to structured data)
        if isinstance(original, str) and isinstance(normalized, dict):
            return True
        
        return False

# Convenience functions
def normalize_extraction_result(result: Dict[str, Any], purpose: str = None, 
                              url: str = None) -> Dict[str, Any]:
    """
    Convenience function to normalize extraction results
    
    Args:
        result: Extraction result dictionary
        purpose: Extraction purpose
        url: Source URL
        
    Returns:
        Normalized result with quality metrics
    """
    
    normalizer = DataNormalizer()
    
    # Extract the actual data
    extracted_data = result.get('extracted_data', result)
    
    # Normalize the data
    normalized_data = normalizer.normalize_extracted_data(extracted_data, purpose, url)
    
    # Calculate quality score
    quality_score = normalizer.calculate_data_quality_score(extracted_data, normalized_data)
    
    # Return enhanced result
    return {
        **result,
        'normalized_data': normalized_data,
        'data_quality_score': quality_score,
        'field_count': len(normalized_data),
        'normalization_applied': True
    }

if __name__ == "__main__":
    # Test the normalizer
    normalizer = DataNormalizer()
    
    test_data = {
        'Company Name': 'Acme Corp Inc.',
        'E-mail': 'Contact@ACME.com',
        'Phone': '(555) 123-4567',
        'Website': 'www.acme.com',
        'Rating': '4.5/5 stars',
        'Price': '$99.99 - $199.99'
    }
    
    normalized = normalizer.normalize_extracted_data(test_data, 'company_info')
    print("Original:", test_data)
    print("Normalized:", normalized)
