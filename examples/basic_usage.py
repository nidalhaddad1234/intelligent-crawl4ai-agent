#!/usr/bin/env python3
"""
Example: Basic Intelligent Scraping
Demonstrates how to use the intelligent agent for various scraping scenarios
"""

import asyncio
import json
from typing import List, Dict, Any

# Example URLs for different scenarios
EXAMPLE_URLS = {
    "business_directories": [
        "https://www.yellowpages.com/new-york-ny/restaurants",
        "https://www.yelp.com/nyc/restaurants",
        "https://foursquare.com/explore?mode=url&ne=40.9176&sw=40.4774&nw=-73.7004&se=-74.2591"
    ],
    "company_websites": [
        "https://www.stripe.com/about",
        "https://www.openai.com/about",
        "https://www.anthropic.com/company"
    ],
    "e_commerce": [
        "https://www.amazon.com/dp/B08N5WRWNW",
        "https://www.etsy.com/listing/1234567890",
        "https://shopify.com/pricing"
    ],
    "news_articles": [
        "https://www.reuters.com/business/",
        "https://techcrunch.com/2024/01/15/ai-news/",
        "https://www.wired.com/story/artificial-intelligence/"
    ]
}

async def basic_website_analysis():
    """Example: Analyze a single website structure"""
    
    print("🔍 Example 1: Website Structure Analysis")
    print("=" * 50)
    
    # This would be called via Claude Desktop MCP
    example_prompt = """
    analyze_website_structure with:
    - url: "https://www.yellowpages.com/new-york-ny/restaurants"
    - purpose: "company_info"
    """
    
    expected_response = {
        "url": "https://www.yellowpages.com/new-york-ny/restaurants",
        "analysis": {
            "website_type": "directory_listing",
            "complexity": "medium",
            "has_javascript": True,
            "has_forms": False,
            "detected_frameworks": ["React"],
            "anti_bot_measures": ["Cloudflare"]
        },
        "recommended_strategy": {
            "primary": "css_extraction",
            "fallbacks": ["llm_extraction"],
            "confidence": 0.85,
            "reasoning": "Directory listings have predictable CSS patterns for business info"
        },
        "extraction_plan": {
            "company_name": "h2, h3, .company-name, .business-name",
            "address": ".address, .location",
            "phone": ".phone, .tel, a[href^='tel:']",
            "website": "a[href^='http']"
        }
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

async def intelligent_single_scraping():
    """Example: Intelligent scraping of multiple URLs"""
    
    print("\n🧠 Example 2: Intelligent Single URL Scraping")
    print("=" * 50)
    
    example_prompt = """
    analyze_and_scrape with:
    - urls: ["https://www.stripe.com/about", "https://www.openai.com/about"]
    - purpose: "company_info"
    - execution_mode: "intelligent_single"
    - additional_context: "Focus on company mission, team size, and contact information"
    """
    
    expected_response = {
        "execution_mode": "intelligent_single",
        "total_urls": 2,
        "processed_urls": 2,
        "successful_extractions": 2,
        "failed_extractions": 0,
        "strategy_distribution": {
            "llm_extraction": 2
        },
        "results": [
            {
                "success": True,
                "url": "https://www.stripe.com/about",
                "strategy_used": "llm_extraction",
                "extracted_data": {
                    "company_name": "Stripe",
                    "mission": "Increase the GDP of the internet",
                    "team_size": "4000+",
                    "headquarters": "San Francisco, CA",
                    "contact_email": "support@stripe.com"
                },
                "confidence_score": 0.92
            },
            {
                "success": True,
                "url": "https://www.openai.com/about",
                "strategy_used": "llm_extraction",
                "extracted_data": {
                    "company_name": "OpenAI",
                    "mission": "Ensure artificial general intelligence benefits all of humanity",
                    "team_size": "1000+",
                    "headquarters": "San Francisco, CA"
                },
                "confidence_score": 0.88
            }
        ],
        "purpose": "company_info"
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

async def high_volume_scraping():
    """Example: High-volume scraping for massive URL lists"""
    
    print("\n⚡ Example 3: High-Volume Scraping")
    print("=" * 50)
    
    # Generate example URL list
    restaurant_urls = [
        f"https://www.yelp.com/biz/restaurant-{i}-new-york"
        for i in range(1, 1001)  # 1000 URLs
    ]
    
    example_prompt = f"""
    submit_high_volume_job with:
    - urls: {restaurant_urls[:5]} ... [995 more URLs]
    - purpose: "company_info"
    - priority: 1
    - batch_size: 100
    - max_workers: 50
    """
    
    expected_response = {
        "job_id": "hvol_1703123456_abc12345",
        "status": "submitted",
        "urls_count": 1000,
        "batch_size": 100,
        "estimated_batches": 10
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

async def job_monitoring():
    """Example: Monitoring high-volume job progress"""
    
    print("\n📊 Example 4: Job Status Monitoring")
    print("=" * 50)
    
    example_prompt = """
    get_job_status with:
    - job_id: "hvol_1703123456_abc12345"
    """
    
    expected_response = {
        "job_id": "hvol_1703123456_abc12345",
        "status": "in_progress",
        "created_at": "2024-01-15T10:30:00Z",
        "started_at": "2024-01-15T10:31:00Z",
        "progress": {
            "total_urls": 1000,
            "processed_urls": 347,
            "successful_urls": 331,
            "failed_urls": 16,
            "remaining_urls": 653,
            "completion_percentage": 34.7
        },
        "performance": {
            "avg_processing_time": 1.2,
            "estimated_completion": 1703127256,
            "processing_rate": "289.5 URLs/minute"
        },
        "metadata": {
            "purpose": "company_info",
            "priority": 1,
            "batch_size": 100,
            "max_workers": 50
        }
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

async def semantic_search_example():
    """Example: Searching previously scraped data"""
    
    print("\n🔍 Example 5: Semantic Search of Extracted Data")
    print("=" * 50)
    
    example_prompt = """
    query_extracted_data with:
    - query: "restaurants in Manhattan with high ratings and delivery"
    - data_type: "company_info"
    - limit: 10
    """
    
    expected_response = {
        "query": "restaurants in Manhattan with high ratings and delivery",
        "results_count": 10,
        "results": [
            {
                "content": "Joe's Pizza - Manhattan location with 4.8 stars, offers delivery",
                "metadata": {
                    "url": "https://www.yelp.com/biz/joes-pizza-manhattan",
                    "purpose": "company_info",
                    "timestamp": 1703123456
                },
                "similarity": 0.92
            },
            {
                "content": "Katz's Delicatessen - Famous NYC deli, 4.6 stars, delivery available",
                "metadata": {
                    "url": "https://www.yelp.com/biz/katzs-delicatessen",
                    "purpose": "company_info",
                    "timestamp": 1703123455
                },
                "similarity": 0.89
            }
        ]
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

async def system_monitoring():
    """Example: Real-time system monitoring"""
    
    print("\n📈 Example 6: System Performance Monitoring")
    print("=" * 50)
    
    example_prompt = """
    get_system_stats
    """
    
    expected_response = {
        "timestamp": 1703123456.789,
        "workers": {
            "total_workers": 50,
            "active_workers": 23,
            "idle_workers": 27,
            "worker_details": [
                {
                    "worker_id": "worker_0",
                    "status": "active",
                    "urls_processed": 1247,
                    "successful_extractions": 1189,
                    "failed_extractions": 58,
                    "success_rate": 95.3,
                    "current_job": "hvol_1703123456_abc12345"
                }
            ]
        },
        "queue": {
            "pending_batches": 7,
            "estimated_urls": 700
        },
        "performance": {
            "urls_processed_last_hour": 17280,
            "avg_processing_time": 1.15,
            "current_throughput": "288.0 URLs/minute"
        },
        "system": {
            "redis_connected": True,
            "database_connected": True
        }
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

async def authentication_example():
    """Example: Scraping with authentication"""
    
    print("\n🔐 Example 7: Authenticated Scraping")
    print("=" * 50)
    
    example_prompt = """
    analyze_and_scrape with:
    - urls: ["https://www.linkedin.com/company/openai/"]
    - purpose: "company_info"
    - execution_mode: "authenticated"
    - credentials: {
        "username": "user@example.com",
        "password": "secure_password"
    }
    """
    
    expected_response = {
        "execution_mode": "authenticated",
        "authentication_used": "simple_login",
        "scraping_result": {
            "success": True,
            "url": "https://www.linkedin.com/company/openai/",
            "extracted_data": {
                "company_name": "OpenAI",
                "industry": "Artificial Intelligence",
                "employees": "1000+",
                "headquarters": "San Francisco, California",
                "followers": "2.1M"
            },
            "authentication_required": True,
            "login_successful": True
        }
    }
    
    print("Claude Desktop Prompt:")
    print(example_prompt)
    print("\nExpected Response:")
    print(json.dumps(expected_response, indent=2))

def common_use_cases():
    """Document common use cases and their optimal configurations"""
    
    print("\n📋 Common Use Cases")
    print("=" * 50)
    
    use_cases = {
        "Business Directory Mining": {
            "description": "Extract company information from business directories",
            "urls": "Yellow Pages, Yelp, Google Business listings",
            "purpose": "company_info",
            "mode": "high_volume",
            "expected_success_rate": "85-95%",
            "optimal_settings": {
                "batch_size": 100,
                "max_workers": 30,
                "strategy": "css_extraction with llm_extraction fallback"
            }
        },
        
        "Contact Discovery": {
            "description": "Find contact information from company websites",
            "urls": "Company websites, About pages, Contact pages",
            "purpose": "contact_discovery",
            "mode": "intelligent_single",
            "expected_success_rate": "70-85%",
            "optimal_settings": {
                "strategy": "llm_extraction",
                "additional_context": "Focus on email addresses, phone numbers, and social links"
            }
        },
        
        "Product Research": {
            "description": "Extract product information and pricing",
            "urls": "E-commerce sites, product pages",
            "purpose": "product_data",
            "mode": "high_volume",
            "expected_success_rate": "80-90%",
            "optimal_settings": {
                "batch_size": 50,
                "max_workers": 40,
                "strategy": "json_css_extraction with structured data"
            }
        },
        
        "Social Media Profiles": {
            "description": "Extract professional profile information",
            "urls": "LinkedIn, Twitter, company social pages",
            "purpose": "profile_info",
            "mode": "authenticated",
            "expected_success_rate": "60-80%",
            "optimal_settings": {
                "strategy": "llm_extraction",
                "requires_authentication": True,
                "anti_detection": "high"
            }
        },
        
        "News and Content": {
            "description": "Extract articles, news, and content",
            "urls": "News sites, blogs, press releases",
            "purpose": "news_content",
            "mode": "intelligent_single",
            "expected_success_rate": "90-95%",
            "optimal_settings": {
                "strategy": "llm_extraction",
                "focus": "headline, content, author, date"
            }
        }
    }
    
    for use_case, details in use_cases.items():
        print(f"\n{use_case}:")
        print(f"  Description: {details['description']}")
        print(f"  Purpose: {details['purpose']}")
        print(f"  Mode: {details['mode']}")
        print(f"  Success Rate: {details['expected_success_rate']}")
        print(f"  Settings: {json.dumps(details['optimal_settings'], indent=4)}")

async def main():
    """Run all examples"""
    
    print("🚀 Intelligent Crawl4AI Agent - Usage Examples")
    print("=" * 60)
    print("These examples show how to use the agent via Claude Desktop MCP interface\n")
    
    await basic_website_analysis()
    await intelligent_single_scraping()
    await high_volume_scraping()
    await job_monitoring()
    await semantic_search_example()
    await system_monitoring()
    await authentication_example()
    common_use_cases()
    
    print("\n" + "=" * 60)
    print("💡 Tips for Best Results:")
    print("- Use specific, descriptive prompts")
    print("- Include additional context when needed")
    print("- Monitor job progress for high-volume tasks")
    print("- Leverage semantic search for data analysis")
    print("- Use authentication mode for protected content")
    print("\n🔗 For more examples, see: examples/ directory")

if __name__ == "__main__":
    asyncio.run(main())
