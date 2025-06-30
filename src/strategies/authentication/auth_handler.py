#!/usr/bin/env python3
"""
Authentication Strategy
Handle login and authentication workflows

Examples:
- Login to LinkedIn for profile access
- Authenticate with Google/Facebook OAuth
- Handle two-factor authentication
- Maintain session across multiple requests
- Handle subscription-based content access
"""

import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.authentication.auth_handler")


class AuthenticationStrategy(BaseExtractionStrategy):
    """
    Handle login and authentication workflows
    
    Examples:
    - Login to LinkedIn for profile access
    - Authenticate with Google/Facebook OAuth
    - Handle two-factor authentication
    - Maintain session across multiple requests
    - Handle subscription-based content access
    """
    
    def __init__(self, credentials: Dict[str, str] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.credentials = credentials or {}
        
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect authentication requirements
            auth_info = self._detect_authentication_requirements(soup, html_content, url)
            
            # Create authentication plan
            auth_plan = self._create_authentication_plan(auth_info, url, context)
            
            extracted_data = {
                "authentication_required": auth_info.get("requires_auth", False),
                "auth_type": auth_info.get("auth_type", "none"),
                "auth_plan": auth_plan,
                "login_form_detected": auth_info.get("has_login_form", False),
                "oauth_providers": auth_info.get("oauth_providers", [])
            }
            
            confidence = 0.9 if auth_info.get("requires_auth") else 0.2
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=True,  # Always successful at detecting auth requirements
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="AuthenticationStrategy",
                execution_time=execution_time,
                metadata={
                    "auth_detected": auth_info.get("requires_auth", False),
                    "auth_complexity": auth_info.get("complexity", "simple")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AuthenticationStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_authentication_requirements(self, soup: BeautifulSoup, html_content: str, url: str) -> Dict[str, Any]:
        """Detect authentication requirements and methods"""
        
        auth_info = {
            "requires_auth": False,
            "auth_type": "none",
            "has_login_form": False,
            "oauth_providers": [],
            "complexity": "simple"
        }
        
        # Check for login indicators
        login_indicators = [
            "login", "sign in", "log in", "authentication",
            "please sign in", "access denied", "unauthorized"
        ]
        
        page_text = html_content.lower()
        if any(indicator in page_text for indicator in login_indicators):
            auth_info["requires_auth"] = True
        
        # Check for login forms
        login_forms = soup.select("form:has([type='password']), .login-form, .signin-form")
        if login_forms:
            auth_info["has_login_form"] = True
            auth_info["requires_auth"] = True
            auth_info["auth_type"] = "form_login"
        
        # Check for OAuth providers
        oauth_patterns = {
            "google": ["google", "gmail"],
            "facebook": ["facebook", "fb"],
            "twitter": ["twitter"],
            "linkedin": ["linkedin"],
            "microsoft": ["microsoft", "outlook"],
            "github": ["github"]
        }
        
        for provider, patterns in oauth_patterns.items():
            if any(pattern in page_text for pattern in patterns):
                if any(oauth_term in page_text for oauth_term in ["oauth", "sign in with", "continue with"]):
                    auth_info["oauth_providers"].append(provider)
                    auth_info["auth_type"] = "oauth"
                    auth_info["requires_auth"] = True
        
        # Check for 2FA indicators
        tfa_indicators = ["two-factor", "2fa", "verification code", "authenticator"]
        if any(indicator in page_text for indicator in tfa_indicators):
            auth_info["complexity"] = "two_factor"
        
        # Check for subscription walls
        subscription_indicators = ["subscribe", "premium", "upgrade", "paywall"]
        if any(indicator in page_text for indicator in subscription_indicators):
            auth_info["auth_type"] = "subscription"
            auth_info["complexity"] = "subscription_required"
        
        # Platform-specific detection
        auth_info.update(self._detect_platform_specific_auth(url, soup))
        
        return auth_info
    
    def _detect_platform_specific_auth(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect platform-specific authentication patterns"""
        
        platform_info = {}
        
        if "linkedin.com" in url:
            if soup.select(".authwall, .guest-homepage"):
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "linkedin_login",
                    "complexity": "professional_network"
                })
        
        elif "facebook.com" in url:
            if "login" in soup.get_text().lower():
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "facebook_login",
                    "complexity": "social_network"
                })
        
        elif "twitter.com" in url or "x.com" in url:
            if soup.select(".login-form, .signin-form"):
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "twitter_login",
                    "complexity": "social_network"
                })
        
        return platform_info
    
    def _create_authentication_plan(self, auth_info: Dict[str, Any], url: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create authentication execution plan"""
        
        plan = {
            "steps": [],
            "estimated_time": 30,  # seconds
            "success_indicators": [],
            "failure_indicators": []
        }
        
        if not auth_info.get("requires_auth"):
            return plan
        
        auth_type = auth_info.get("auth_type")
        credentials = context.get("credentials", {}) if context else {}
        combined_creds = {**self.credentials, **credentials}
        
        if auth_type == "form_login":
            plan["steps"] = [
                {
                    "action": "fill_username",
                    "selector": "[name='username'], [name='email'], [type='email']",
                    "value": combined_creds.get("username", "")
                },
                {
                    "action": "fill_password",
                    "selector": "[name='password'], [type='password']",
                    "value": combined_creds.get("password", "")
                },
                {
                    "action": "submit_form",
                    "selector": "[type='submit'], .login-button, .signin-button"
                }
            ]
        
        elif auth_type == "oauth":
            provider = auth_info.get("oauth_providers", ["google"])[0]
            plan["steps"] = [
                {
                    "action": "click_oauth_button",
                    "selector": f".{provider}-login, [data-provider='{provider}']",
                    "provider": provider
                },
                {
                    "action": "handle_oauth_redirect",
                    "wait_for_redirect": True,
                    "timeout": 30000
                }
            ]
        
        # Add 2FA handling if needed
        if auth_info.get("complexity") == "two_factor":
            plan["steps"].append({
                "action": "handle_2fa",
                "selector": "[name='code'], [name='verification_code']",
                "wait_for_prompt": True,
                "code_source": combined_creds.get("2fa_method", "manual")
            })
        
        # Define success/failure indicators
        plan["success_indicators"] = [
            "dashboard", "profile", "logged in", "welcome",
            ".user-menu", ".logout", ".account-menu"
        ]
        
        plan["failure_indicators"] = [
            "invalid", "incorrect", "failed", "error",
            ".error-message", ".login-error"
        ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Authentication strategy confidence"""
        
        # Check for authentication indicators
        auth_indicators = [
            "login", "sign in", "authentication", "password",
            "access denied", "unauthorized"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in auth_indicators if indicator in content_lower)
        
        confidence = min(indicator_count * 0.2, 0.9)
        
        # Higher confidence for known platforms requiring auth
        protected_domains = ["linkedin.com", "facebook.com", "twitter.com"]
        if any(domain in url for domain in protected_domains):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Authentication supports access-controlled purposes"""
        supported_purposes = [
            "profile_info", "social_media_analysis", "premium_content",
            "subscription_data", "protected_resources", "member_content"
        ]
        return purpose in supported_purposes
