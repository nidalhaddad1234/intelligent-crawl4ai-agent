"""
Extractor Tool - AI-discoverable data extraction capabilities

This tool provides various extraction strategies for different types of content
including structured data, tables, contact info, and pattern-based extraction.
"""

import re
import json
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

from ..registry import ai_tool, create_example


@ai_tool(
    name="extract_structured_data",
    description="Extract structured data from HTML/text using schemas or patterns",
    category="extraction",
    examples=[
        create_example(
            "Extract product information",
            html_content="<div class='product'><h1>iPhone 15</h1><span class='price'>$999</span></div>",
            schema={
                "name": "h1",
                "price": ".price"
            }
        ),
        create_example(
            "Extract article metadata",
            text_content="Published: 2024-01-15 | Author: John Doe | Category: Technology",
            pattern="published|author|category"
        )
    ],
    capabilities=[
        "Extract data using CSS selectors",
        "Extract data using regex patterns",
        "Schema-based extraction",
        "Handle nested structures",
        "Clean and normalize extracted data",
        "Extract from HTML, JSON, or plain text"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def extract_structured_data(
    content: str,
    content_type: str = "html",
    schema: Optional[Dict[str, str]] = None,
    pattern: Optional[str] = None,
    clean_text: bool = True
) -> Dict[str, Any]:
    """
    Extract structured data from content using schemas or patterns
    
    Args:
        content: The content to extract from
        content_type: Type of content - 'html', 'json', 'text'
        schema: CSS selector schema for HTML extraction
        pattern: Regex pattern for text extraction
        clean_text: Whether to clean extracted text
        
    Returns:
        Dictionary with extracted data
    """
    try:
        extracted_data = {}
        
        if content_type == "html" and schema:
            soup = BeautifulSoup(content, 'html.parser')
            
            for field, selector in schema.items():
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        value = elements[0].get_text(strip=True) if clean_text else elements[0].get_text()
                    else:
                        value = [el.get_text(strip=True) if clean_text else el.get_text() for el in elements]
                    extracted_data[field] = value
                    
        elif content_type == "json":
            try:
                data = json.loads(content)
                extracted_data = data if isinstance(data, dict) else {"data": data}
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON: {str(e)}"}
                
        elif content_type == "text" and pattern:
            # Extract using regex pattern
            matches = re.findall(f"({pattern}):\\s*([^|\\n]+)", content, re.IGNORECASE)
            for key, value in matches:
                extracted_data[key.lower()] = value.strip()
        
        return {
            "success": True,
            "data": extracted_data,
            "fields_extracted": len(extracted_data),
            "content_type": content_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "content_type": content_type
        }


@ai_tool(
    name="extract_tables",
    description="Extract tabular data from HTML tables or text",
    category="extraction",
    examples=[
        create_example(
            "Extract pricing table",
            html_content="<table><tr><th>Product</th><th>Price</th></tr><tr><td>iPhone</td><td>$999</td></tr></table>",
            table_index=0
        ),
        create_example(
            "Extract all tables from page",
            html_content="<table>...</table><table>...</table>",
            extract_all=True
        )
    ],
    capabilities=[
        "Extract HTML tables as structured data",
        "Handle complex table structures",
        "Extract specific tables by index",
        "Convert tables to various formats",
        "Handle nested tables",
        "Extract table metadata"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def extract_tables(
    html_content: str,
    table_index: Optional[int] = None,
    extract_all: bool = False,
    output_format: str = "dict"
) -> Dict[str, Any]:
    """
    Extract tables from HTML content
    
    Args:
        html_content: HTML content containing tables
        table_index: Specific table index to extract (0-based)
        extract_all: Extract all tables
        output_format: Output format - 'dict', 'list', 'dataframe'
        
    Returns:
        Dictionary with extracted table data
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')
        
        if not tables:
            return {
                "success": True,
                "tables_found": 0,
                "data": []
            }
        
        extracted_tables = []
        
        # Determine which tables to extract
        if extract_all:
            tables_to_extract = enumerate(tables)
        elif table_index is not None:
            if table_index < len(tables):
                tables_to_extract = [(table_index, tables[table_index])]
            else:
                return {
                    "success": False,
                    "error": f"Table index {table_index} out of range. Found {len(tables)} tables."
                }
        else:
            tables_to_extract = [(0, tables[0])]  # Default to first table
        
        for idx, table in tables_to_extract:
            # Extract headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
            
            # Extract rows
            rows = []
            for tr in table.find_all('tr')[1:]:  # Skip header row
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            # Format output
            if output_format == "dict" and headers:
                table_data = []
                for row in rows:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            row_dict[header] = row[i]
                    table_data.append(row_dict)
            elif output_format == "dataframe":
                import pandas as pd
                table_data = pd.DataFrame(rows, columns=headers if headers else None).to_dict('records')
            else:
                table_data = {
                    "headers": headers,
                    "rows": rows
                }
            
            extracted_tables.append({
                "table_index": idx,
                "rows_count": len(rows),
                "columns_count": len(headers) if headers else (len(rows[0]) if rows else 0),
                "data": table_data
            })
        
        return {
            "success": True,
            "tables_found": len(tables),
            "tables_extracted": len(extracted_tables),
            "data": extracted_tables[0]["data"] if len(extracted_tables) == 1 else extracted_tables
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@ai_tool(
    name="extract_contact_info",
    description="Extract contact information like emails, phones, addresses from content",
    category="extraction",
    examples=[
        create_example(
            "Extract all contact details",
            content="Contact us at info@example.com or call +1-555-123-4567. Visit us at 123 Main St, City, State 12345"
        ),
        create_example(
            "Extract specific contact type",
            content="Email: support@company.com, sales@company.com",
            contact_types=["email"]
        )
    ],
    capabilities=[
        "Extract email addresses",
        "Extract phone numbers (various formats)",
        "Extract physical addresses",
        "Extract social media handles",
        "Extract contact forms info",
        "Validate extracted contacts"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def extract_contact_info(
    content: str,
    contact_types: Optional[List[str]] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Extract contact information from content
    
    Args:
        content: Content to extract from (HTML or text)
        contact_types: Specific types to extract ['email', 'phone', 'address', 'social']
        validate: Whether to validate extracted info
        
    Returns:
        Dictionary with extracted contact information
    """
    try:
        # Remove HTML tags if present
        if '<' in content and '>' in content:
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text()
        else:
            text = content
        
        # Default to all types if not specified
        if not contact_types:
            contact_types = ['email', 'phone', 'address', 'social']
        
        extracted = {}
        
        # Email extraction
        if 'email' in contact_types:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = list(set(re.findall(email_pattern, text)))
            
            if validate:
                # Basic email validation
                emails = [e for e in emails if '@' in e and '.' in e.split('@')[1]]
            
            if emails:
                extracted['emails'] = emails
        
        # Phone extraction
        if 'phone' in contact_types:
            # Multiple phone patterns
            phone_patterns = [
                r'\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',  # US format
                r'\+?[0-9]{1,3}[-.\s]?[0-9]{3,14}',  # International
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Simple format
            ]
            
            phones = []
            for pattern in phone_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    if isinstance(matches[0], tuple):
                        phones.extend([''.join(m) for m in matches])
                    else:
                        phones.extend(matches)
            
            phones = list(set(phones))
            
            if validate:
                # Basic phone validation (at least 10 digits)
                phones = [p for p in phones if len(re.sub(r'\D', '', p)) >= 10]
            
            if phones:
                extracted['phones'] = phones
        
        # Address extraction
        if 'address' in contact_types:
            # Simple address pattern (number + street + city/state/zip)
            address_pattern = r'\b\d{1,5}\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Plaza|Pl)\.?\s*,?\s*[A-Za-z\s]+,?\s*[A-Z]{2}?\s*\d{5}?\b'
            addresses = re.findall(address_pattern, text, re.IGNORECASE)
            
            if addresses:
                extracted['addresses'] = list(set(addresses))
        
        # Social media extraction
        if 'social' in contact_types:
            social_patterns = {
                'twitter': r'(?:twitter\.com/|@)([A-Za-z0-9_]+)',
                'linkedin': r'linkedin\.com/(?:in|company)/([A-Za-z0-9-]+)',
                'facebook': r'facebook\.com/([A-Za-z0-9.]+)',
                'instagram': r'instagram\.com/([A-Za-z0-9_.]+)',
            }
            
            social_handles = {}
            for platform, pattern in social_patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    social_handles[platform] = list(set(matches))
            
            if social_handles:
                extracted['social_media'] = social_handles
        
        return {
            "success": True,
            "contact_info": extracted,
            "types_found": list(extracted.keys()),
            "total_contacts": sum(len(v) if isinstance(v, list) else len(v.values()) for v in extracted.values())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@ai_tool(
    name="extract_lists",
    description="Extract list items from HTML or text content",
    category="extraction",
    examples=[
        create_example(
            "Extract product features",
            html_content="<ul><li>Feature 1</li><li>Feature 2</li><li>Feature 3</li></ul>",
            list_type="ul"
        ),
        create_example(
            "Extract numbered steps",
            text_content="1. First step\n2. Second step\n3. Third step",
            list_type="numbered"
        )
    ],
    capabilities=[
        "Extract HTML lists (ul, ol)",
        "Extract numbered lists from text",
        "Extract bullet points",
        "Handle nested lists",
        "Extract definition lists",
        "Custom list patterns"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def extract_lists(
    content: str,
    list_type: Optional[str] = None,
    css_selector: Optional[str] = None,
    pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract lists from content
    
    Args:
        content: HTML or text content
        list_type: Type of list - 'ul', 'ol', 'numbered', 'bullet', 'all'
        css_selector: CSS selector for specific lists
        pattern: Custom regex pattern for list items
        
    Returns:
        Dictionary with extracted lists
    """
    try:
        lists = []
        
        # Check if HTML
        if '<' in content and '>' in content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract HTML lists
            if not list_type or list_type in ['ul', 'ol', 'all']:
                if css_selector:
                    list_elements = soup.select(css_selector)
                else:
                    list_elements = soup.find_all(['ul', 'ol'])
                
                for list_elem in list_elements:
                    items = []
                    for li in list_elem.find_all('li', recursive=False):
                        # Handle nested lists
                        text = li.get_text(strip=True)
                        nested = li.find(['ul', 'ol'])
                        if nested:
                            nested_items = [ni.get_text(strip=True) for ni in nested.find_all('li')]
                            items.append({
                                "text": text.replace(nested.get_text(), '').strip(),
                                "nested": nested_items
                            })
                        else:
                            items.append(text)
                    
                    if items:
                        lists.append({
                            "type": list_elem.name,
                            "items": items,
                            "count": len(items)
                        })
            
            # Also check for text patterns in HTML
            text = soup.get_text()
        else:
            text = content
        
        # Extract numbered lists from text
        if not list_type or list_type in ['numbered', 'all']:
            numbered_pattern = r'^\s*(\d+)[.)]\s*(.+)$'
            lines = text.split('\n')
            current_list = []
            
            for line in lines:
                match = re.match(numbered_pattern, line)
                if match:
                    current_list.append(match.group(2).strip())
                elif current_list:
                    # End of list
                    lists.append({
                        "type": "numbered",
                        "items": current_list,
                        "count": len(current_list)
                    })
                    current_list = []
            
            if current_list:
                lists.append({
                    "type": "numbered",
                    "items": current_list,
                    "count": len(current_list)
                })
        
        # Extract bullet points
        if not list_type or list_type in ['bullet', 'all']:
            bullet_pattern = r'^\s*[•·▪▫◦‣⁃]\s*(.+)$'
            lines = text.split('\n')
            bullet_items = []
            
            for line in lines:
                match = re.match(bullet_pattern, line)
                if match:
                    bullet_items.append(match.group(1).strip())
            
            if bullet_items:
                lists.append({
                    "type": "bullet",
                    "items": bullet_items,
                    "count": len(bullet_items)
                })
        
        # Custom pattern
        if pattern:
            custom_items = re.findall(pattern, text, re.MULTILINE)
            if custom_items:
                lists.append({
                    "type": "custom",
                    "items": custom_items,
                    "count": len(custom_items)
                })
        
        return {
            "success": True,
            "lists_found": len(lists),
            "total_items": sum(lst["count"] for lst in lists),
            "lists": lists
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@ai_tool(
    name="extract_metadata",
    description="Extract metadata from HTML pages including meta tags, JSON-LD, and Open Graph",
    category="extraction",
    examples=[
        create_example(
            "Extract page metadata",
            html_content='<head><meta name="description" content="Page description"><title>Page Title</title></head>'
        ),
        create_example(
            "Extract specific metadata",
            html_content='<meta property="og:image" content="image.jpg">',
            metadata_types=["opengraph"]
        )
    ],
    capabilities=[
        "Extract meta tags",
        "Extract Open Graph data",
        "Extract Twitter Card data",
        "Extract JSON-LD structured data",
        "Extract page title and description",
        "Extract canonical URLs"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def extract_metadata(
    html_content: str,
    metadata_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Extract metadata from HTML content
    
    Args:
        html_content: HTML content
        metadata_types: Specific types to extract ['meta', 'opengraph', 'twitter', 'jsonld']
        
    Returns:
        Dictionary with extracted metadata
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Default to all types
        if not metadata_types:
            metadata_types = ['meta', 'opengraph', 'twitter', 'jsonld']
        
        metadata = {}
        
        # Basic metadata
        if 'meta' in metadata_types:
            basic = {}
            
            # Title
            title_tag = soup.find('title')
            if title_tag:
                basic['title'] = title_tag.get_text(strip=True)
            
            # Meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name', '')
                content = meta.get('content', '')
                
                if name and content:
                    basic[name] = content
            
            # Canonical URL
            canonical = soup.find('link', {'rel': 'canonical'})
            if canonical:
                basic['canonical'] = canonical.get('href')
            
            if basic:
                metadata['basic'] = basic
        
        # Open Graph
        if 'opengraph' in metadata_types:
            og = {}
            for meta in soup.find_all('meta', property=re.compile('^og:')):
                property_name = meta.get('property', '').replace('og:', '')
                content = meta.get('content', '')
                if property_name and content:
                    og[property_name] = content
            
            if og:
                metadata['opengraph'] = og
        
        # Twitter Card
        if 'twitter' in metadata_types:
            twitter = {}
            for meta in soup.find_all('meta', attrs={'name': re.compile('^twitter:')}):
                name = meta.get('name', '').replace('twitter:', '')
                content = meta.get('content', '')
                if name and content:
                    twitter[name] = content
            
            if twitter:
                metadata['twitter'] = twitter
        
        # JSON-LD
        if 'jsonld' in metadata_types:
            jsonld_scripts = soup.find_all('script', type='application/ld+json')
            jsonld_data = []
            
            for script in jsonld_scripts:
                try:
                    data = json.loads(script.string)
                    jsonld_data.append(data)
                except json.JSONDecodeError:
                    pass
            
            if jsonld_data:
                metadata['jsonld'] = jsonld_data
        
        return {
            "success": True,
            "metadata": metadata,
            "types_found": list(metadata.keys())
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@ai_tool(
    name="extract_patterns",
    description="Extract data using custom regex patterns",
    category="extraction",
    examples=[
        create_example(
            "Extract product codes",
            content="Products: ABC-123, DEF-456, GHI-789",
            patterns={"product_code": r"[A-Z]{3}-\d{3}"}
        ),
        create_example(
            "Extract dates and amounts",
            content="Invoice dated 2024-01-15 for $1,234.56",
            patterns={
                "date": r"\d{4}-\d{2}-\d{2}",
                "amount": r"\$[\d,]+\.?\d*"
            }
        )
    ],
    capabilities=[
        "Custom regex pattern matching",
        "Multiple pattern extraction",
        "Named group extraction",
        "Pattern validation",
        "Format conversion",
        "Complex pattern combinations"
    ],
    performance={
        "speed": "high",
        "reliability": "medium",
        "cost": "low"
    }
)
async def extract_patterns(
    content: str,
    patterns: Dict[str, str],
    flags: int = re.IGNORECASE,
    first_match_only: bool = False
) -> Dict[str, Any]:
    """
    Extract data using regex patterns
    
    Args:
        content: Content to extract from
        patterns: Dictionary of {name: regex_pattern}
        flags: Regex flags
        first_match_only: Return only first match for each pattern
        
    Returns:
        Dictionary with extracted pattern matches
    """
    try:
        extracted = {}
        
        for name, pattern in patterns.items():
            try:
                if first_match_only:
                    match = re.search(pattern, content, flags)
                    if match:
                        # Handle named groups
                        if match.groups():
                            extracted[name] = match.groups()
                        else:
                            extracted[name] = match.group(0)
                else:
                    matches = re.findall(pattern, content, flags)
                    if matches:
                        extracted[name] = matches
                        
            except re.error as e:
                return {
                    "success": False,
                    "error": f"Invalid regex pattern for '{name}': {str(e)}"
                }
        
        return {
            "success": True,
            "extracted": extracted,
            "patterns_matched": len(extracted),
            "total_matches": sum(
                len(v) if isinstance(v, list) else 1 
                for v in extracted.values()
            )
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@ai_tool(
    name="extract_by_proximity",
    description="Extract values near keywords or labels",
    category="extraction",
    examples=[
        create_example(
            "Extract values after labels",
            content="Price: $99.99 | Discount: 20% | Stock: 15 units",
            keywords=["Price", "Discount", "Stock"],
            proximity_chars=20
        )
    ],
    capabilities=[
        "Extract values near keywords",
        "Handle various label-value formats",
        "Configurable proximity distance",
        "Multiple keyword extraction",
        "Smart value detection"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def extract_by_proximity(
    content: str,
    keywords: List[str],
    proximity_chars: int = 50,
    value_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Extract values that appear near specified keywords
    
    Args:
        content: Content to extract from
        keywords: Keywords to search near
        proximity_chars: Maximum characters to look ahead
        value_patterns: Optional patterns for values
        
    Returns:
        Dictionary with extracted values
    """
    try:
        extracted = {}
        
        # Default value patterns
        if not value_patterns:
            value_patterns = [
                r'\$?[\d,]+\.?\d*%?',  # Numbers, prices, percentages
                r'[A-Za-z0-9\s]+(?=\s*[|\n])',  # Text before separator
                r'[^:|\n]+',  # Any text until separator
            ]
        
        for keyword in keywords:
            # Find keyword positions
            pattern = re.compile(re.escape(keyword) + r'\s*:?\s*', re.IGNORECASE)
            
            for match in pattern.finditer(content):
                start = match.end()
                end = min(start + proximity_chars, len(content))
                text_after = content[start:end]
                
                # Try to extract value
                for value_pattern in value_patterns:
                    value_match = re.search(value_pattern, text_after)
                    if value_match:
                        value = value_match.group(0).strip()
                        if value:
                            extracted[keyword] = value
                            break
        
        return {
            "success": True,
            "extracted": extracted,
            "keywords_found": len(extracted)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
