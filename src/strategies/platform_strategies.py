#!/usr/bin/env python3
"""
Platform-Specific Extraction Strategies
Specialized strategies for major platforms and websites
"""

import asyncio
import json
import time
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from .base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class YelpStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for Yelp business listings and reviews
    
    Examples:
    - Extract restaurant details from Yelp business pages
    - Get review data and ratings
    - Scrape business contact information and hours
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.yelp_selectors = {
            "business_name": [
                "h1[data-testid='page-title']",
                ".biz-page-title",
                "h1.lemon--h1__373c0__2ZHSL"
            ],
            "rating": [
                "[aria-label*='star rating']",
                ".i-stars",
                "[data-testid='rating']"
            ],
            "review_count": [
                "[data-testid='review-count']",
                ".review-count",
                "a[href*='#reviews']"
            ],
            "price_range": [
                "[data-testid='price-range']",
                ".price-range",
                ".business-attribute-price-range"
            ],
            "categories": [
                "[data-testid='category']",
                ".category-str-list a",
                ".business-categories"
            ],
            "address": [
                "[data-testid='business-address']",
                ".street-address",
                "address"
            ],
            "phone": [
                "[data-testid='phone-number']",
                ".biz-phone",
                "a[href^='tel:']"
            ],
            "website": [
                "[data-testid='business-website-link']",
                ".biz-website a",
                "a[href*='biz_redir']"
            ],
            "hours": [
                "[data-testid='hours']",
                ".hours-table",
                ".business-hours"
            ],
            "photos": [
                "[data-testid='photo-box'] img",
                ".photo-box img",
                ".showcase-photos img"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if this is a business page or search results
            if self._is_business_page(url):
                extracted_data = await self._extract_business_details(soup, url)
            else:
                extracted_data = await self._extract_search_results(soup, url)
            
            # Extract structured data if available
            structured_data = self._extract_yelp_structured_data(html_content)
            if structured_data:
                extracted_data.update(structured_data)
            
            confidence = self.calculate_confidence(extracted_data, ["business_name", "rating", "address"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="YelpStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": "business" if self._is_business_page(url) else "search",
                    "yelp_specific": True
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="YelpStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _is_business_page(self, url: str) -> bool:
        """Check if URL is a Yelp business page vs search results"""
        return '/biz/' in url
    
    async def _extract_business_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract details from a Yelp business page"""
        business = {}
        
        # Extract basic business information
        for field, selectors in self.yelp_selectors.items():
            value = self._extract_yelp_field(soup, selectors, field)
            if value:
                business[field] = value
        
        # Extract reviews data
        reviews_data = self._extract_reviews_data(soup)
        if reviews_data:
            business["reviews"] = reviews_data
        
        # Extract business attributes
        attributes = self._extract_business_attributes(soup)
        if attributes:
            business["attributes"] = attributes
        
        # Extract menu information if available
        menu_data = self._extract_menu_data(soup)
        if menu_data:
            business["menu"] = menu_data
        
        return business
    
    async def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract business listings from Yelp search results"""
        results = {"businesses": []}
        
        # Find business listing containers
        business_containers = soup.select(".businessName, .search-result, [data-testid='serp-ia-card']")
        
        for container in business_containers[:20]:  # Limit to first 20 results
            business = {}
            
            # Extract basic info from each listing
            name_elem = container.select_one("h3 a, .businessName a, [data-testid='business-name']")
            if name_elem:
                business["name"] = name_elem.get_text(strip=True)
                business["url"] = name_elem.get('href', '')
            
            # Rating and review count
            rating_elem = container.select_one("[aria-label*='star'], .i-stars")
            if rating_elem:
                business["rating"] = self._extract_rating_from_element(rating_elem)
            
            review_elem = container.select_one(".reviewCount, [data-testid='review-count']")
            if review_elem:
                business["review_count"] = review_elem.get_text(strip=True)
            
            # Categories
            category_elem = container.select_one(".category-str-list, .business-categories")
            if category_elem:
                business["categories"] = category_elem.get_text(strip=True)
            
            # Address
            address_elem = container.select_one(".address, .neighborhood-str-list")
            if address_elem:
                business["address"] = address_elem.get_text(strip=True)
            
            if business.get("name"):
                results["businesses"].append(business)
        
        return results
    
    def _extract_yelp_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Yelp-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "rating":
                    return self._extract_rating_from_element(element)
                elif field_type == "photos":
                    return self._extract_photo_urls(elements)
                elif field_type == "website":
                    return self._extract_yelp_website(element)
                elif field_type == "phone":
                    return self._extract_phone_number(element)
                else:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_rating_from_element(self, element) -> Optional[str]:
        """Extract rating from Yelp rating element"""
        # Check aria-label first
        aria_label = element.get('aria-label', '')
        if 'star' in aria_label:
            # Extract number from "4.5 star rating"
            rating_match = re.search(r'(\d+\.?\d*)', aria_label)
            if rating_match:
                return rating_match.group(1)
        
        # Check for data attributes
        for attr in ['data-rating', 'data-star-rating']:
            if element.get(attr):
                return element.get(attr)
        
        # Check text content
        text = element.get_text(strip=True)
        rating_match = re.search(r'(\d+\.?\d*)', text)
        if rating_match:
            return rating_match.group(1)
        
        return None
    
    def _extract_photo_urls(self, elements) -> List[str]:
        """Extract photo URLs from elements"""
        photos = []
        for element in elements:
            src = element.get('src') or element.get('data-src')
            if src and src.startswith('http'):
                photos.append(src)
        return photos[:10]  # Limit to first 10 photos
    
    def _extract_yelp_website(self, element) -> Optional[str]:
        """Extract website URL from Yelp business link"""
        href = element.get('href', '')
        if 'biz_redir' in href:
            # Parse the redirect URL to get actual website
            try:
                parsed = urlparse(href)
                query_params = parse_qs(parsed.query)
                if 'url' in query_params:
                    return query_params['url'][0]
            except:
                pass
        return href if href.startswith('http') else None
    
    def _extract_phone_number(self, element) -> Optional[str]:
        """Extract phone number from element"""
        href = element.get('href', '')
        if href.startswith('tel:'):
            return href.replace('tel:', '')
        return element.get_text(strip=True)
    
    def _extract_reviews_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract review-related data"""
        reviews_data = {}
        
        # Total review count
        review_count_elem = soup.select_one("[data-testid='review-count'], .review-count")
        if review_count_elem:
            reviews_data["total_reviews"] = review_count_elem.get_text(strip=True)
        
        # Individual reviews
        review_elements = soup.select(".review, [data-testid='review']")
        if review_elements:
            reviews = []
            for review_elem in review_elements[:5]:  # First 5 reviews
                review = {}
                
                # Reviewer name
                name_elem = review_elem.select_one(".user-name, .reviewer-name")
                if name_elem:
                    review["reviewer"] = name_elem.get_text(strip=True)
                
                # Review rating
                rating_elem = review_elem.select_one("[aria-label*='star']")
                if rating_elem:
                    review["rating"] = self._extract_rating_from_element(rating_elem)
                
                # Review text
                text_elem = review_elem.select_one(".review-content, .comment")
                if text_elem:
                    review["text"] = text_elem.get_text(strip=True)[:500]  # Limit length
                
                if review:
                    reviews.append(review)
            
            reviews_data["recent_reviews"] = reviews
        
        return reviews_data
    
    def _extract_business_attributes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract business attributes like amenities, parking, etc."""
        attributes = {}
        
        # Look for attributes section
        attr_sections = soup.select(".business-attributes, .amenities-info")
        
        for section in attr_sections:
            attr_items = section.select(".attribute-item, .amenity-item")
            for item in attr_items:
                key_elem = item.select_one(".attribute-key, .amenity-key")
                value_elem = item.select_one(".attribute-value, .amenity-value")
                
                if key_elem and value_elem:
                    key = key_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    attributes[key] = value
        
        return attributes
    
    def _extract_menu_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract menu information if available"""
        menu_data = {}
        
        # Look for menu sections
        menu_sections = soup.select(".menu-section, .menu-items")
        
        for section in menu_sections:
            section_name_elem = section.select_one(".section-header, .menu-section-header")
            section_name = section_name_elem.get_text(strip=True) if section_name_elem else "Menu"
            
            items = []
            menu_items = section.select(".menu-item")
            
            for item in menu_items[:10]:  # Limit items per section
                item_data = {}
                
                name_elem = item.select_one(".menu-item-name, .item-name")
                if name_elem:
                    item_data["name"] = name_elem.get_text(strip=True)
                
                price_elem = item.select_one(".menu-item-price, .item-price")
                if price_elem:
                    item_data["price"] = price_elem.get_text(strip=True)
                
                desc_elem = item.select_one(".menu-item-description, .item-description")
                if desc_elem:
                    item_data["description"] = desc_elem.get_text(strip=True)
                
                if item_data:
                    items.append(item_data)
            
            if items:
                menu_data[section_name] = items
        
        return menu_data
    
    def _extract_yelp_structured_data(self, html_content: str) -> Dict[str, Any]:
        """Extract Yelp-specific structured data"""
        structured = {}
        
        # Look for Yelp's JSON data in script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            script_text = script.get_text()
            if 'window.yelp' in script_text or 'bizDetails' in script_text:
                # Try to extract JSON data
                try:
                    # Look for JSON objects in the script
                    json_matches = re.findall(r'\{[^{}]*"bizId"[^{}]*\}', script_text)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'bizId' in data:
                                structured['yelp_internal_data'] = data
                                break
                        except json.JSONDecodeError:
                            continue
                except Exception:
                    continue
        
        return structured
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Yelp strategy has high confidence on Yelp URLs"""
        if 'yelp.com' in url:
            return 0.9
        return 0.1  # Very low confidence for non-Yelp URLs
    
    def supports_purpose(self, purpose: str) -> bool:
        """Yelp strategy supports business and review extraction"""
        supported_purposes = [
            "company_info", "business_listings", "contact_discovery",
            "review_analysis", "local_business_data"
        ]
        return purpose in supported_purposes

class LinkedInStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for LinkedIn profiles and company pages
    
    Examples:
    - Extract professional profile information
    - Get company details and employee counts
    - Scrape job postings and company updates
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.linkedin_selectors = {
            # Profile selectors
            "profile_name": [
                "h1.text-heading-xlarge",
                ".pv-text-details__left-panel h1",
                ".top-card-layout__title"
            ],
            "profile_headline": [
                ".text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium",
                ".top-card-layout__headline"
            ],
            "profile_location": [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small",
                ".top-card-layout__first-subline"
            ],
            "profile_summary": [
                ".pv-about-section .pv-about__summary-text",
                "[data-section='summary']",
                ".about-section .about-section__text"
            ],
            "profile_experience": [
                ".pv-experience-section .pv-entity__summary-info",
                "[data-section='experience'] .pv-entity__summary-info"
            ],
            "profile_education": [
                ".pv-education-section .pv-entity__summary-info",
                "[data-section='education'] .pv-entity__summary-info"
            ],
            "profile_connections": [
                ".pv-top-card--list-bullet .pv-top-card--list-bullet",
                ".top-card-layout__first-subline button"
            ],
            
            # Company selectors
            "company_name": [
                ".org-top-card-summary__title",
                ".top-card-layout__entity-info h1"
            ],
            "company_description": [
                ".org-about-us-organization-description__text",
                ".about-section__description"
            ],
            "company_industry": [
                ".org-top-card-summary__industry",
                ".top-card-layout__headline"
            ],
            "company_size": [
                ".org-about-company-module__company-size-definition-text",
                ".company-size .text-body-small"
            ],
            "company_location": [
                ".org-top-card-summary__headquarters",
                ".headquarters .text-body-small"
            ],
            "company_website": [
                ".org-about-us-organization-description__website a",
                ".website .link-without-visited-state"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if this is a profile or company page
            if '/in/' in url:
                extracted_data = await self._extract_profile_data(soup, url)
            elif '/company/' in url:
                extracted_data = await self._extract_company_data(soup, url)
            else:
                # Try to detect based on content
                extracted_data = await self._extract_general_linkedin_data(soup, url)
            
            # Check for login wall
            if self._is_login_wall(soup):
                extracted_data["requires_authentication"] = True
                extracted_data["access_limited"] = True
            
            confidence = self.calculate_confidence(extracted_data, ["profile_name", "company_name"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="LinkedInStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": self._detect_page_type(url),
                    "requires_auth": extracted_data.get("requires_authentication", False)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="LinkedInStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _extract_profile_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract LinkedIn profile data"""
        profile = {}
        
        # Basic profile information
        for field, selectors in self.linkedin_selectors.items():
            if field.startswith('profile_'):
                value = self._extract_linkedin_field(soup, selectors, field)
                if value:
                    clean_field = field.replace('profile_', '')
                    profile[clean_field] = value
        
        # Extract experience details
        experience_data = self._extract_experience_section(soup)
        if experience_data:
            profile["experience_details"] = experience_data
        
        # Extract education details
        education_data = self._extract_education_section(soup)
        if education_data:
            profile["education_details"] = education_data
        
        # Extract skills
        skills_data = self._extract_skills_section(soup)
        if skills_data:
            profile["skills"] = skills_data
        
        return profile
    
    async def _extract_company_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract LinkedIn company data"""
        company = {}
        
        # Basic company information
        for field, selectors in self.linkedin_selectors.items():
            if field.startswith('company_'):
                value = self._extract_linkedin_field(soup, selectors, field)
                if value:
                    clean_field = field.replace('company_', '')
                    company[clean_field] = value
        
        # Extract employee data
        employee_data = self._extract_employee_data(soup)
        if employee_data:
            company["employees"] = employee_data
        
        # Extract recent updates
        updates_data = self._extract_company_updates(soup)
        if updates_data:
            company["recent_updates"] = updates_data
        
        return company
    
    async def _extract_general_linkedin_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract general LinkedIn data when page type is unclear"""
        data = {}
        
        # Try both profile and company extraction
        profile_data = await self._extract_profile_data(soup, url)
        company_data = await self._extract_company_data(soup, url)
        
        if profile_data:
            data.update(profile_data)
        if company_data:
            data.update(company_data)
        
        return data
    
    def _extract_linkedin_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using LinkedIn-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "profile_connections":
                    return self._extract_connection_count(element)
                elif field_type == "company_size":
                    return self._extract_employee_count(element)
                else:
                    text = element.get_text(strip=True)
                    if text and len(text) > 1:
                        return text
        return None
    
    def _extract_connection_count(self, element) -> Optional[str]:
        """Extract connection count from LinkedIn element"""
        text = element.get_text(strip=True)
        
        # Look for patterns like "500+ connections"
        connection_patterns = [
            r'(\d+\+?)\s+connections?',
            r'(\d+\+?)\s+contacts?'
        ]
        
        for pattern in connection_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_employee_count(self, element) -> Optional[str]:
        """Extract employee count from LinkedIn company page"""
        text = element.get_text(strip=True)
        
        # Look for patterns like "1,001-5,000 employees"
        employee_patterns = [
            r'([\d,]+-[\d,]+)\s+employees?',
            r'(\d+[\d,]*)\s+employees?'
        ]
        
        for pattern in employee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_experience_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract detailed experience information"""
        experiences = []
        
        experience_items = soup.select(".pv-entity__summary-info, .experience-item")
        
        for item in experience_items[:10]:  # Limit to 10 experiences
            exp = {}
            
            # Job title
            title_elem = item.select_one("h3, .pv-entity__summary-title")
            if title_elem:
                exp["title"] = title_elem.get_text(strip=True)
            
            # Company name
            company_elem = item.select_one(".pv-entity__secondary-title, .company-name")
            if company_elem:
                exp["company"] = company_elem.get_text(strip=True)
            
            # Duration
            duration_elem = item.select_one(".pv-entity__bullet-item, .duration")
            if duration_elem:
                exp["duration"] = duration_elem.get_text(strip=True)
            
            # Location
            location_elem = item.select_one(".pv-entity__location, .location")
            if location_elem:
                exp["location"] = location_elem.get_text(strip=True)
            
            if exp:
                experiences.append(exp)
        
        return experiences
    
    def _extract_education_section(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract detailed education information"""
        education = []
        
        education_items = soup.select(".pv-education-entity, .education-item")
        
        for item in education_items[:5]:  # Limit to 5 education entries
            edu = {}
            
            # School name
            school_elem = item.select_one("h3, .pv-entity__school-name")
            if school_elem:
                edu["school"] = school_elem.get_text(strip=True)
            
            # Degree
            degree_elem = item.select_one(".pv-entity__degree-name, .degree")
            if degree_elem:
                edu["degree"] = degree_elem.get_text(strip=True)
            
            # Field of study
            field_elem = item.select_one(".pv-entity__fos, .field-of-study")
            if field_elem:
                edu["field"] = field_elem.get_text(strip=True)
            
            # Years
            years_elem = item.select_one(".pv-entity__dates, .years")
            if years_elem:
                edu["years"] = years_elem.get_text(strip=True)
            
            if edu:
                education.append(edu)
        
        return education
    
    def _extract_skills_section(self, soup: BeautifulSoup) -> List[str]:
        """Extract skills from LinkedIn profile"""
        skills = []
        
        skill_elements = soup.select(".pv-skill-category-entity__name, .skill-name")
        
        for elem in skill_elements[:20]:  # Limit to 20 skills
            skill = elem.get_text(strip=True)
            if skill:
                skills.append(skill)
        
        return skills
    
    def _extract_employee_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract employee information from company page"""
        employee_data = {}
        
        # Look for employee count
        count_elem = soup.select_one(".org-about-company-module__company-size-definition-text")
        if count_elem:
            employee_data["total_employees"] = count_elem.get_text(strip=True)
        
        # Look for notable employees
        employee_elements = soup.select(".org-people-profile-card, .employee-card")
        if employee_elements:
            notable_employees = []
            for emp_elem in employee_elements[:10]:
                name_elem = emp_elem.select_one(".org-people-profile-card__profile-title, .name")
                title_elem = emp_elem.select_one(".org-people-profile-card__profile-subtitle, .title")
                
                if name_elem:
                    emp_info = {"name": name_elem.get_text(strip=True)}
                    if title_elem:
                        emp_info["title"] = title_elem.get_text(strip=True)
                    notable_employees.append(emp_info)
            
            employee_data["notable_employees"] = notable_employees
        
        return employee_data
    
    def _extract_company_updates(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract recent company updates"""
        updates = []
        
        update_elements = soup.select(".update-item, .company-update")
        
        for update_elem in update_elements[:5]:  # Limit to 5 updates
            update = {}
            
            # Update text
            text_elem = update_elem.select_one(".update-text, .post-content")
            if text_elem:
                update["content"] = text_elem.get_text(strip=True)[:500]  # Limit length
            
            # Update date
            date_elem = update_elem.select_one(".update-date, .post-date")
            if date_elem:
                update["date"] = date_elem.get_text(strip=True)
            
            if update:
                updates.append(update)
        
        return updates
    
    def _is_login_wall(self, soup: BeautifulSoup) -> bool:
        """Check if page shows LinkedIn login wall"""
        login_indicators = [
            ".join-form", ".login-form", ".guest-login",
            "Join LinkedIn", "Sign in", "authwall"
        ]
        
        page_text = soup.get_text().lower()
        
        for indicator in login_indicators:
            if indicator.lower() in page_text:
                return True
        
        # Check for specific LinkedIn auth wall elements
        auth_elements = soup.select(".authwall, .guest-homepage, .join-form")
        return len(auth_elements) > 0
    
    def _detect_page_type(self, url: str) -> str:
        """Detect LinkedIn page type from URL"""
        if '/in/' in url:
            return "profile"
        elif '/company/' in url:
            return "company"
        elif '/jobs/' in url:
            return "jobs"
        elif '/school/' in url:
            return "school"
        else:
            return "unknown"
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """LinkedIn strategy has high confidence on LinkedIn URLs"""
        if 'linkedin.com' in url:
            # Lower confidence if login wall detected
            if 'authwall' in html_content or 'join-form' in html_content:
                return 0.6
            return 0.9
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """LinkedIn strategy supports professional and company data"""
        supported_purposes = [
            "profile_info", "company_info", "professional_profiles",
            "business_intelligence", "recruitment_data", "contact_discovery"
        ]
        return purpose in supported_purposes

class AmazonStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for Amazon product pages and search results
    
    Examples:
    - Extract product details, pricing, and reviews
    - Get seller information and shipping details
    - Scrape product specifications and images
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.amazon_selectors = {
            "product_title": [
                "#productTitle",
                ".product-title",
                "h1.a-size-large"
            ],
            "price": [
                ".a-price-whole",
                "#price_inside_buybox",
                ".a-price.a-text-price.a-size-medium.apexPriceToPay"
            ],
            "rating": [
                ".a-icon-alt",
                "[data-hook='average-star-rating']",
                ".acrPopover"
            ],
            "review_count": [
                "#acrCustomerReviewText",
                "[data-hook='total-review-count']"
            ],
            "availability": [
                "#availability span",
                ".a-color-success",
                ".a-color-state"
            ],
            "brand": [
                "#bylineInfo",
                ".a-brand",
                "[data-brand]"
            ],
            "description": [
                "#feature-bullets ul",
                ".a-unordered-list.a-vertical",
                "#productDescription"
            ],
            "images": [
                "#landingImage",
                ".a-dynamic-image",
                "#altImages img"
            ],
            "specifications": [
                "#productDetails_detailBullets_sections1",
                ".a-keyvalue",
                "#prodDetails"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if this is a product page or search results
            if '/dp/' in url or '/gp/product/' in url:
                extracted_data = await self._extract_product_details(soup, url)
            elif '/s?' in url:
                extracted_data = await self._extract_search_results(soup, url)
            else:
                extracted_data = await self._extract_general_amazon_data(soup, url)
            
            confidence = self.calculate_confidence(extracted_data, ["product_title", "price"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="AmazonStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": self._detect_amazon_page_type(url),
                    "amazon_specific": True
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AmazonStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _extract_product_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Amazon product details"""
        product = {}
        
        # Extract basic product information
        for field, selectors in self.amazon_selectors.items():
            value = self._extract_amazon_field(soup, selectors, field)
            if value:
                product[field] = value
        
        # Extract seller information
        seller_data = self._extract_seller_info(soup)
        if seller_data:
            product["seller"] = seller_data
        
        # Extract shipping information
        shipping_data = self._extract_shipping_info(soup)
        if shipping_data:
            product["shipping"] = shipping_data
        
        # Extract variant information (size, color, etc.)
        variants_data = self._extract_variants_info(soup)
        if variants_data:
            product["variants"] = variants_data
        
        return product
    
    async def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Amazon search results"""
        results = {"products": []}
        
        # Find product containers in search results
        product_containers = soup.select("[data-component-type='s-search-result']")
        
        for container in product_containers[:20]:  # Limit to first 20 results
            product = {}
            
            # Product title and link
            title_elem = container.select_one("h2 a span, .s-size-mini span")
            if title_elem:
                product["title"] = title_elem.get_text(strip=True)
            
            link_elem = container.select_one("h2 a")
            if link_elem:
                product["url"] = link_elem.get('href', '')
            
            # Price
            price_elem = container.select_one(".a-price-whole, .a-price")
            if price_elem:
                product["price"] = price_elem.get_text(strip=True)
            
            # Rating
            rating_elem = container.select_one(".a-icon-alt")
            if rating_elem:
                product["rating"] = self._extract_amazon_rating(rating_elem)
            
            # Image
            img_elem = container.select_one("img.s-image")
            if img_elem:
                product["image"] = img_elem.get('src', '')
            
            if product.get("title"):
                results["products"].append(product)
        
        return results
    
    async def _extract_general_amazon_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract general Amazon data for unclear page types"""
        data = {}
        
        # Try product extraction first
        product_data = await self._extract_product_details(soup, url)
        if product_data:
            data.update(product_data)
        
        # Try search results extraction
        search_data = await self._extract_search_results(soup, url)
        if search_data and search_data.get("products"):
            data.update(search_data)
        
        return data
    
    def _extract_amazon_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Amazon-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "rating":
                    return self._extract_amazon_rating(element)
                elif field_type == "price":
                    return self._extract_amazon_price(element)
                elif field_type == "images":
                    return self._extract_amazon_images(elements)
                elif field_type == "description":
                    return self._extract_amazon_description(element)
                else:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_amazon_rating(self, element) -> Optional[str]:
        """Extract rating from Amazon rating element"""
        # Check alt text for rating
        alt_text = element.get('alt', '')
        if 'out of 5 stars' in alt_text:
            rating_match = re.search(r'(\d+\.?\d*)', alt_text)
            if rating_match:
                return rating_match.group(1)
        
        # Check text content
        text = element.get_text(strip=True)
        rating_match = re.search(r'(\d+\.?\d*)', text)
        if rating_match:
            return rating_match.group(1)
        
        return None
    
    def _extract_amazon_price(self, element) -> Optional[str]:
        """Extract price from Amazon price element"""
        # Try to get the full price
        price_text = element.get_text(strip=True)
        
        # Clean up price text
        price_text = re.sub(r'[^\d.,]', '', price_text)
        
        if price_text:
            return price_text
        
        return None
    
    def _extract_amazon_images(self, elements) -> List[str]:
        """Extract product images from Amazon"""
        images = []
        
        for element in elements:
            src = element.get('src') or element.get('data-src')
            if src and src.startswith('http'):
                images.append(src)
        
        return images[:5]  # Limit to first 5 images
    
    def _extract_amazon_description(self, element) -> Optional[str]:
        """Extract product description from Amazon"""
        # For bullet points, join them
        if element.name == 'ul':
            bullets = element.select('li')
            descriptions = [li.get_text(strip=True) for li in bullets]
            return ' | '.join(descriptions)
        else:
            return element.get_text(strip=True)
    
    def _extract_seller_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract seller information"""
        seller_data = {}
        
        # Seller name
        seller_elem = soup.select_one("#sellerProfileTriggerId, .a-link-normal")
        if seller_elem:
            seller_data["name"] = seller_elem.get_text(strip=True)
        
        # Fulfilled by Amazon
        fulfillment_elem = soup.select_one("#merchant-info")
        if fulfillment_elem and "amazon" in fulfillment_elem.get_text().lower():
            seller_data["fulfilled_by_amazon"] = True
        
        return seller_data
    
    def _extract_shipping_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract shipping information"""
        shipping_data = {}
        
        # Delivery date
        delivery_elem = soup.select_one("#mir-layout-DELIVERY_BLOCK")
        if delivery_elem:
            shipping_data["delivery_info"] = delivery_elem.get_text(strip=True)
        
        # Shipping cost
        shipping_elem = soup.select_one(".a-color-secondary.a-text-bold")
        if shipping_elem and "shipping" in shipping_elem.get_text().lower():
            shipping_data["cost"] = shipping_elem.get_text(strip=True)
        
        return shipping_data
    
    def _extract_variants_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product variants (size, color, etc.)"""
        variants = {}
        
        # Size variants
        size_elements = soup.select("#variation_size_name .selection")
        if size_elements:
            sizes = [elem.get_text(strip=True) for elem in size_elements]
            variants["sizes"] = sizes
        
        # Color variants
        color_elements = soup.select("#variation_color_name .selection")
        if color_elements:
            colors = [elem.get_text(strip=True) for elem in color_elements]
            variants["colors"] = colors
        
        return variants
    
    def _detect_amazon_page_type(self, url: str) -> str:
        """Detect Amazon page type from URL"""
        if '/dp/' in url or '/gp/product/' in url:
            return "product"
        elif '/s?' in url:
            return "search"
        elif '/stores/' in url:
            return "store"
        else:
            return "unknown"
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Amazon strategy has high confidence on Amazon URLs"""
        if 'amazon.com' in url or 'amazon.' in url:
            return 0.9
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """Amazon strategy supports product and e-commerce data"""
        supported_purposes = [
            "product_data", "price_monitoring", "ecommerce_analysis",
            "competitive_intelligence", "review_analysis"
        ]
        return purpose in supported_purposes

class YellowPagesStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for Yellow Pages business directory
    
    Examples:
    - Extract business listings from Yellow Pages search results
    - Get detailed business information from business pages
    - Scrape contact information and business hours
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.yellowpages_selectors = {
            "business_name": [
                ".business-name h3 a",
                ".listing-name",
                "h1.dockable"
            ],
            "phone": [
                ".phones.phone.primary",
                ".phone",
                "a[href^='tel:']"
            ],
            "address": [
                ".street-address",
                ".listing-address",
                ".address"
            ],
            "website": [
                ".track-visit-website",
                ".website-link a",
                "a[href*='http']"
            ],
            "categories": [
                ".categories a",
                ".business-categories",
                ".category"
            ],
            "rating": [
                ".rating .count",
                ".star-rating",
                ".result-rating"
            ],
            "years_in_business": [
                ".years-in-business",
                ".business-age"
            ],
            "hours": [
                ".hours-info",
                ".business-hours",
                ".opening-hours"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if search results or business page
            if '/search/' in url or 'find_loc=' in url:
                extracted_data = await self._extract_search_results(soup, url)
            else:
                extracted_data = await self._extract_business_details(soup, url)
            
            confidence = self.calculate_confidence(extracted_data, ["business_name", "phone", "address"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="YellowPagesStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": "search" if "/search/" in url else "business"
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="YellowPagesStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Yellow Pages search results"""
        results = {"businesses": []}
        
        # Find business listing containers
        business_containers = soup.select(".result, .search-results .listing")
        
        for container in business_containers[:30]:  # Get first 30 results
            business = {}
            
            # Extract data using selectors
            for field, selectors in self.yellowpages_selectors.items():
                value = self._extract_yp_field(container, selectors, field)
                if value:
                    business[field] = value
            
            if business.get("business_name"):
                results["businesses"].append(business)
        
        return results
    
    async def _extract_business_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed business information"""
        business = {}
        
        # Extract all available fields
        for field, selectors in self.yellowpages_selectors.items():
            value = self._extract_yp_field(soup, selectors, field)
            if value:
                business[field] = value
        
        # Extract additional details
        business_details = self._extract_additional_details(soup)
        if business_details:
            business.update(business_details)
        
        return business
    
    def _extract_yp_field(self, container, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Yellow Pages specific logic"""
        for selector in selectors:
            elements = container.select(selector)
            for element in elements:
                if field_type == "phone":
                    return self._extract_yp_phone(element)
                elif field_type == "website":
                    return self._extract_yp_website(element)
                elif field_type == "rating":
                    return self._extract_yp_rating(element)
                else:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_yp_phone(self, element) -> Optional[str]:
        """Extract phone number from Yellow Pages element"""
        href = element.get('href', '')
        if href.startswith('tel:'):
            return href.replace('tel:', '')
        
        text = element.get_text(strip=True)
        # Clean phone number
        phone_match = re.search(r'(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})', text)
        if phone_match:
            return phone_match.group(1)
        
        return text if text else None
    
    def _extract_yp_website(self, element) -> Optional[str]:
        """Extract website URL from Yellow Pages element"""
        href = element.get('href', '')
        if href and href.startswith('http'):
            return href
        return None
    
    def _extract_yp_rating(self, element) -> Optional[str]:
        """Extract rating from Yellow Pages element"""
        text = element.get_text(strip=True)
        rating_match = re.search(r'(\d+\.?\d*)', text)
        if rating_match:
            return rating_match.group(1)
        return None
    
    def _extract_additional_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional business details"""
        details = {}
        
        # Business description
        desc_elem = soup.select_one(".business-description, .about-business")
        if desc_elem:
            details["description"] = desc_elem.get_text(strip=True)
        
        # Payment methods
        payment_elem = soup.select_one(".payment-methods")
        if payment_elem:
            details["payment_methods"] = payment_elem.get_text(strip=True)
        
        # Services
        services_elems = soup.select(".services li, .business-services li")
        if services_elems:
            services = [elem.get_text(strip=True) for elem in services_elems]
            details["services"] = services
        
        return details
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Yellow Pages strategy confidence"""
        if 'yellowpages.com' in url:
            return 0.9
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """Yellow Pages supports business directory purposes"""
        supported_purposes = [
            "company_info", "business_listings", "contact_discovery",
            "local_business_data", "directory_mining"
        ]
        return purpose in supported_purposes

class GoogleBusinessStrategy(BaseExtractionStrategy):
    """
    Strategy for Google Business listings and maps data
    
    Examples:
    - Extract business information from Google My Business listings
    - Get reviews and ratings from Google Maps
    - Scrape business hours and contact information
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.google_selectors = {
            "business_name": [
                "h1[data-attrid='title']",
                ".SPZz6b",
                ".x3AX1-LfntMc-header-title-title"
            ],
            "rating": [
                "[data-attrid='kc:/location/location:rating']",
                ".yi40Hd.YrbPuc",
                ".Aq14fc"
            ],
            "review_count": [
                "[data-attrid='kc:/location/location:num_reviews']",
                ".hqzQac",
                ".RDApEe.YrbPuc"
            ],
            "address": [
                "[data-attrid='kc:/location/location:address']",
                ".LrzXr",
                ".T6pBCe"
            ],
            "phone": [
                "[data-attrid='kc:/location/location:phone']",
                ".LrzXr.zdqRlf.kno-fv",
                "a[href^='tel:']"
            ],
            "website": [
                "[data-attrid='kc:/location/location:website']",
                ".CL9Uqc.Ab5aWb",
                "a[data-dtype='d3website']"
            ],
            "hours": [
                "[data-attrid='kc:/location/location:hours']",
                ".t39EBf.GUrTXd",
                ".OqQkV"
            ],
            "category": [
                "[data-attrid='kc:/location/location:category']",
                ".YhemCb",
                ".mgr77e"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract business information
            for field, selectors in self.google_selectors.items():
                value = self._extract_google_field(soup, selectors, field)
                if value:
                    extracted_data[field] = value
            
            # Extract reviews if available
            reviews_data = self._extract_google_reviews(soup)
            if reviews_data:
                extracted_data["reviews"] = reviews_data
            
            confidence = self.calculate_confidence(extracted_data, ["business_name", "rating"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="GoogleBusinessStrategy",
                execution_time=execution_time,
                metadata={
                    "google_business": True
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="GoogleBusinessStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_google_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Google-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "phone":
                    href = element.get('href', '')
                    if href.startswith('tel:'):
                        return href.replace('tel:', '')
                
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_google_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract Google reviews"""
        reviews = []
        
        # Look for review elements
        review_elements = soup.select(".jftiEf, .review-item")
        
        for review_elem in review_elements[:5]:  # First 5 reviews
            review = {}
            
            # Reviewer name
            name_elem = review_elem.select_one(".X43Kjb, .reviewer-name")
            if name_elem:
                review["reviewer"] = name_elem.get_text(strip=True)
            
            # Review text
            text_elem = review_elem.select_one(".wiI7pd, .review-text")
            if text_elem:
                review["text"] = text_elem.get_text(strip=True)[:300]
            
            # Review rating
            rating_elem = review_elem.select_one(".kvMYJc, .review-rating")
            if rating_elem:
                rating_text = rating_elem.get('aria-label', '')
                rating_match = re.search(r'(\d+)', rating_text)
                if rating_match:
                    review["rating"] = rating_match.group(1)
            
            if review:
                reviews.append(review)
        
        return reviews
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Google Business strategy confidence"""
        if 'google.com' in url and ('maps' in url or 'business' in url):
            return 0.8
        return 0.2
    
    def supports_purpose(self, purpose: str) -> bool:
        """Google Business supports local business purposes"""
        supported_purposes = [
            "company_info", "business_listings", "contact_discovery",
            "local_business_data", "review_analysis"
        ]
        return purpose in supported_purposes

class FacebookStrategy(BaseExtractionStrategy):
    """
    Strategy for Facebook pages and business profiles
    
    Examples:
    - Extract Facebook page information
    - Get business details from Facebook pages
    - Scrape posts and engagement data
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.facebook_selectors = {
            "page_name": [
                "h1[data-testid='page_title']",
                ".x1heor9g.x1qlqyl8.x1pd3egz.x1a2a7pz",
                ".page-title"
            ],
            "page_category": [
                "[data-testid='page_subtitle']",
                ".x193iq5w.xeuugli.x13faqbe",
                ".page-category"
            ],
            "page_likes": [
                "[data-testid='page_likes']",
                ".page-likes-count"
            ],
            "page_followers": [
                "[data-testid='page_followers']",
                ".page-followers-count"
            ],
            "about_info": [
                "[data-testid='page_about_description']",
                ".page-about",
                ".about-section"
            ],
            "contact_info": [
                ".contact-info",
                ".page-contact"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract page information
            for field, selectors in self.facebook_selectors.items():
                value = self._extract_facebook_field(soup, selectors, field)
                if value:
                    extracted_data[field] = value
            
            # Check for login requirement
            if self._requires_facebook_login(soup):
                extracted_data["requires_authentication"] = True
            
            confidence = self.calculate_confidence(extracted_data, ["page_name"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="FacebookStrategy",
                execution_time=execution_time,
                metadata={
                    "facebook_page": True,
                    "requires_auth": extracted_data.get("requires_authentication", False)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FacebookStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_facebook_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Facebook-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _requires_facebook_login(self, soup: BeautifulSoup) -> bool:
        """Check if Facebook login is required"""
        login_indicators = [
            "Log in to Facebook",
            "Create Account",
            "login_form"
        ]
        
        page_text = soup.get_text()
        return any(indicator in page_text for indicator in login_indicators)
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Facebook strategy confidence"""
        if 'facebook.com' in url:
            return 0.7
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """Facebook supports social media and business purposes"""
        supported_purposes = [
            "company_info", "social_media_analysis", "business_intelligence",
            "contact_discovery", "brand_monitoring"
        ]
        return purpose in supported_purposes
