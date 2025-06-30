#!/usr/bin/env python3
"""
LinkedIn Strategy
Specialized strategy for LinkedIn profiles and company pages

Examples:
- Extract professional profile information
- Get company details and employee counts
- Scrape job postings and company updates
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.platforms.social_networks.linkedin")


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
