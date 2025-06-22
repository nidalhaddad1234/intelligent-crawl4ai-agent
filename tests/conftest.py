#!/usr/bin/env python3
"""
Test Configuration and Fixtures
Provides common test utilities, fixtures, and mock data for the intelligent scraping agent
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock

# Test data and fixtures
@pytest.fixture
def sample_html_directory():
    """Sample HTML content for directory listing page"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Business Directory - New York Restaurants</title></head>
    <body>
        <div class="search-results">
            <div class="listing" data-business="restaurant-1">
                <h3 class="business-name"><a href="/business/joes-pizza">Joe's Pizza</a></h3>
                <div class="address">123 Main St, New York, NY 10001</div>
                <div class="phone"><a href="tel:+15551234567">(555) 123-4567</a></div>
                <div class="rating">4.5 stars</div>
                <div class="categories">Pizza, Italian</div>
            </div>
            <div class="listing" data-business="restaurant-2">
                <h3 class="business-name"><a href="/business/sushi-place">Best Sushi Place</a></h3>
                <div class="address">456 Oak Ave, New York, NY 10002</div>
                <div class="phone"><a href="tel:+15559876543">(555) 987-6543</a></div>
                <div class="rating">4.8 stars</div>
                <div class="categories">Sushi, Japanese</div>
            </div>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_ecommerce():
    """Sample HTML content for e-commerce product page"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Wireless Headphones - Best Electronics Store</title></head>
    <body>
        <div class="product-container">
            <h1 id="productTitle">Premium Wireless Headphones</h1>
            <div class="price">$99.99</div>
            <div class="rating">4.3 out of 5 stars</div>
            <div class="review-count">1,247 reviews</div>
            <div class="brand">TechBrand</div>
            <div class="description">
                High-quality wireless headphones with noise cancellation
            </div>
            <div class="availability">In Stock</div>
            <img class="product-image" src="/images/headphones.jpg" alt="Wireless Headphones">
        </div>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Premium Wireless Headphones",
            "brand": "TechBrand",
            "offers": {
                "@type": "Offer",
                "price": "99.99",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        }
        </script>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_news():
    """Sample HTML content for news article"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Breaking: Tech Industry News</title></head>
    <body>
        <article>
            <h1 class="headline">AI Technology Reaches New Milestone</h1>
            <div class="author">By Jane Smith</div>
            <time datetime="2024-01-15T10:30:00Z" class="published">January 15, 2024</time>
            <div class="article-content">
                <p>Artificial intelligence technology has reached a significant milestone today...</p>
                <p>Industry experts believe this development will transform how we work...</p>
            </div>
            <div class="tags">AI, Technology, Innovation</div>
        </article>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_linkedin():
    """Sample HTML content for LinkedIn profile"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>John Doe - Software Engineer - LinkedIn</title></head>
    <body>
        <div class="profile-section">
            <h1 class="text-heading-xlarge">John Doe</h1>
            <div class="text-body-medium break-words">Senior Software Engineer at TechCorp</div>
            <div class="text-body-small inline t-black--light break-words">San Francisco, CA</div>
            <div class="connections">500+ connections</div>
        </div>
        <div class="about-section">
            <div class="pv-about__summary-text">
                Experienced software engineer specializing in AI and machine learning...
            </div>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_form():
    """Sample HTML content with contact form"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Contact Us - Example Company</title></head>
    <body>
        <form id="contact-form" action="/submit-contact" method="POST">
            <div class="form-group">
                <label for="name">Full Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="email">Email Address:</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="company">Company:</label>
                <input type="text" id="company" name="company">
            </div>
            <div class="form-group">
                <label for="message">Message:</label>
                <textarea id="message" name="message" rows="4" required></textarea>
            </div>
            <button type="submit" class="submit-btn">Send Message</button>
        </form>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_pagination():
    """Sample HTML content with pagination"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Search Results - Page 1 of 10</title></head>
    <body>
        <div class="results">
            <div class="item">Result 1</div>
            <div class="item">Result 2</div>
            <div class="item">Result 3</div>
        </div>
        <div class="pagination">
            <span class="current">1</span>
            <a href="/search?page=2">2</a>
            <a href="/search?page=3">3</a>
            <a href="/search?page=2" class="next">Next</a>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing"""
    mock_client = AsyncMock()
    mock_client.generate = AsyncMock(return_value='{"test": "response"}')
    mock_client.embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3])
    mock_client.health_check = AsyncMock(return_value=True)
    mock_client.initialize = AsyncMock()
    return mock_client

@pytest.fixture
def mock_chromadb_manager():
    """Mock ChromaDB manager for testing"""
    mock_manager = AsyncMock()
    mock_manager.store_extraction_result = AsyncMock()
    mock_manager.query_similar_strategies = AsyncMock(return_value=[])
    mock_manager.semantic_search = AsyncMock(return_value={"results": []})
    mock_manager.initialize = AsyncMock()
    return mock_manager

@pytest.fixture
def mock_crawler_result():
    """Mock Crawl4AI result for testing"""
    mock_result = Mock()
    mock_result.html = "<html><body>Test content</body></html>"
    mock_result.cleaned_html = "Test content"
    mock_result.extracted_content = '{"test": "data"}'
    mock_result.metadata = {"title": "Test Page", "description": "Test description"}
    mock_result.links = ["http://example.com/link1", "http://example.com/link2"]
    return mock_result

@pytest.fixture
def sample_extraction_contexts():
    """Sample extraction contexts for different purposes"""
    return {
        "company_info": {
            "purpose": "company_info",
            "additional_context": "Focus on business details and contact information"
        },
        "contact_discovery": {
            "purpose": "contact_discovery",
            "additional_context": "Find all possible contact methods"
        },
        "product_data": {
            "purpose": "product_data",
            "additional_context": "Extract pricing and specifications"
        },
        "form_automation": {
            "purpose": "form_automation",
            "form_data": {
                "name": "Test User",
                "email": "test@example.com",
                "company": "Test Corp"
            }
        }
    }

@pytest.fixture
def sample_urls():
    """Sample URLs for different website types"""
    return {
        "yelp_business": "https://www.yelp.com/biz/joes-pizza-new-york",
        "yelp_search": "https://www.yelp.com/search?find_desc=restaurants&find_loc=New+York",
        "linkedin_profile": "https://www.linkedin.com/in/john-doe",
        "linkedin_company": "https://www.linkedin.com/company/techcorp",
        "amazon_product": "https://www.amazon.com/dp/B08N5WRWNW",
        "amazon_search": "https://www.amazon.com/s?k=wireless+headphones",
        "yellowpages": "https://www.yellowpages.com/new-york-ny/restaurants",
        "google_business": "https://www.google.com/maps/place/Example+Business",
        "generic_corporate": "https://www.example-corp.com/about",
        "news_article": "https://www.example-news.com/ai-breakthrough-2024"
    }

@pytest.fixture
def expected_extractions():
    """Expected extraction results for validation"""
    return {
        "directory_listing": {
            "businesses": [
                {
                    "name": "Joe's Pizza",
                    "address": "123 Main St, New York, NY 10001",
                    "phone": "(555) 123-4567",
                    "rating": "4.5 stars",
                    "category": "Pizza, Italian"
                }
            ]
        },
        "ecommerce_product": {
            "product_title": "Premium Wireless Headphones",
            "price": "$99.99",
            "rating": "4.3",
            "brand": "TechBrand",
            "description": "High-quality wireless headphones with noise cancellation"
        },
        "news_article": {
            "headline": "AI Technology Reaches New Milestone",
            "author": "Jane Smith",
            "publish_date": "January 15, 2024",
            "content": "Artificial intelligence technology has reached a significant milestone today..."
        },
        "contact_form": {
            "forms_detected": 1,
            "target_forms": 1,
            "completion_plan": [
                {
                    "form_type": "contact_form",
                    "completion_steps": [
                        {"action": "fill_field", "field_name": "name"},
                        {"action": "fill_field", "field_name": "email"},
                        {"action": "submit_form"}
                    ]
                }
            ]
        }
    }

# Utility functions for tests
def create_mock_strategy_result(success: bool = True, data: Dict[str, Any] = None, 
                               confidence: float = 0.8, strategy: str = "TestStrategy") -> Dict[str, Any]:
    """Create a mock strategy result for testing"""
    return {
        "success": success,
        "extracted_data": data or {},
        "confidence_score": confidence,
        "strategy_used": strategy,
        "execution_time": 1.5,
        "metadata": {"test": True}
    }

def assert_strategy_result_valid(result, expected_success: bool = True):
    """Assert that a strategy result has the expected structure"""
    assert hasattr(result, 'success')
    assert hasattr(result, 'extracted_data')
    assert hasattr(result, 'confidence_score')
    assert hasattr(result, 'strategy_used')
    assert hasattr(result, 'execution_time')
    assert hasattr(result, 'metadata')
    
    assert result.success == expected_success
    assert isinstance(result.extracted_data, dict)
    assert 0.0 <= result.confidence_score <= 1.0
    assert isinstance(result.strategy_used, str)
    assert result.execution_time >= 0

def assert_extraction_contains_fields(extracted_data: Dict[str, Any], expected_fields: List[str]):
    """Assert that extracted data contains expected fields"""
    for field in expected_fields:
        assert field in extracted_data, f"Expected field '{field}' not found in extracted data"
        assert extracted_data[field] is not None, f"Field '{field}' is None"
        assert str(extracted_data[field]).strip(), f"Field '{field}' is empty"

# Performance testing utilities
class PerformanceTimer:
    """Utility for measuring performance in tests"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.end_time = time.time()
        return self.elapsed_time
    
    @property
    def elapsed_time(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

def assert_performance_acceptable(elapsed_time: float, max_time: float):
    """Assert that operation completed within acceptable time"""
    assert elapsed_time <= max_time, f"Operation took {elapsed_time:.2f}s, expected <= {max_time}s"

# Error simulation utilities
class NetworkError(Exception):
    """Simulated network error for testing"""
    pass

class AuthenticationError(Exception):
    """Simulated authentication error for testing"""
    pass

def simulate_network_failure():
    """Simulate network failure for testing error handling"""
    raise NetworkError("Simulated network failure")

def simulate_auth_failure():
    """Simulate authentication failure for testing"""
    raise AuthenticationError("Simulated authentication failure")

# Test data validation
def validate_business_data(business_data: Dict[str, Any]) -> bool:
    """Validate extracted business data structure"""
    required_fields = ["name"]
    optional_fields = ["address", "phone", "rating", "category", "website", "email"]
    
    # Must have at least the business name
    if "name" not in business_data or not business_data["name"]:
        return False
    
    # All fields should be strings or valid data types
    for field, value in business_data.items():
        if field in required_fields + optional_fields:
            if value is not None and not isinstance(value, (str, int, float)):
                return False
    
    return True

def validate_product_data(product_data: Dict[str, Any]) -> bool:
    """Validate extracted product data structure"""
    required_fields = ["product_title"]
    optional_fields = ["price", "rating", "brand", "description", "availability"]
    
    if "product_title" not in product_data or not product_data["product_title"]:
        return False
    
    # Price should be a valid price format if present
    if "price" in product_data and product_data["price"]:
        price_str = str(product_data["price"])
        if not any(char.isdigit() for char in price_str):
            return False
    
    return True

def validate_form_analysis(form_data: Dict[str, Any]) -> bool:
    """Validate form analysis data structure"""
    required_fields = ["forms_detected", "completion_plan"]
    
    for field in required_fields:
        if field not in form_data:
            return False
    
    # forms_detected should be a non-negative integer
    if not isinstance(form_data["forms_detected"], int) or form_data["forms_detected"] < 0:
        return False
    
    # completion_plan should be a list
    if not isinstance(form_data["completion_plan"], list):
        return False
    
    return True

# Configuration for different test environments
TEST_CONFIG = {
    "timeout": {
        "unit_test": 5.0,      # 5 seconds for unit tests
        "integration_test": 30.0,  # 30 seconds for integration tests
        "performance_test": 60.0   # 1 minute for performance tests
    },
    "retry": {
        "network_operations": 3,
        "flaky_tests": 2
    },
    "performance": {
        "strategy_execution": 10.0,    # Max 10 seconds per strategy
        "llm_generation": 30.0,        # Max 30 seconds for LLM calls
        "crawler_operation": 15.0      # Max 15 seconds for crawling
    }
}

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take more than 5 seconds)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "requires_network: marks tests that require network access"
    )

# Asyncio event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
