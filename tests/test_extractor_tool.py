"""
Test ExtractorTool Implementation
"""

import pytest
import asyncio
from ai_core.tools.extractor import (
    extract_structured_data,
    extract_tables,
    extract_contact_info,
    extract_lists,
    extract_metadata,
    extract_patterns,
    extract_by_proximity
)


@pytest.mark.asyncio
async def test_extract_structured_data():
    """Test structured data extraction"""
    html = """
    <div class="product">
        <h1>iPhone 15 Pro</h1>
        <span class="price">$999</span>
        <p class="description">Latest iPhone with A17 Pro chip</p>
    </div>
    """
    
    result = await extract_structured_data(
        content=html,
        content_type="html",
        schema={
            "title": "h1",
            "price": ".price",
            "description": ".description"
        }
    )
    
    assert result["success"] is True
    assert result["data"]["title"] == "iPhone 15 Pro"
    assert result["data"]["price"] == "$999"
    assert "A17 Pro" in result["data"]["description"]


@pytest.mark.asyncio
async def test_extract_tables():
    """Test table extraction"""
    html = """
    <table>
        <tr><th>Product</th><th>Price</th></tr>
        <tr><td>iPhone</td><td>$999</td></tr>
        <tr><td>iPad</td><td>$599</td></tr>
    </table>
    """
    
    result = await extract_tables(html_content=html, output_format="dict")
    
    assert result["success"] is True
    assert result["tables_found"] == 1
    assert len(result["data"]) == 2
    assert result["data"][0]["Product"] == "iPhone"
    assert result["data"][0]["Price"] == "$999"


@pytest.mark.asyncio
async def test_extract_contact_info():
    """Test contact information extraction"""
    content = """
    Contact us at:
    Email: support@example.com or sales@example.com
    Phone: +1-555-123-4567 or (555) 987-6543
    Address: 123 Main Street, Suite 100, New York, NY 10001
    Twitter: @examplecorp
    """
    
    result = await extract_contact_info(content)
    
    assert result["success"] is True
    assert len(result["contact_info"]["emails"]) == 2
    assert "support@example.com" in result["contact_info"]["emails"]
    assert len(result["contact_info"]["phones"]) >= 1
    assert "addresses" in result["contact_info"]


@pytest.mark.asyncio
async def test_extract_lists():
    """Test list extraction"""
    html = """
    <h2>Features:</h2>
    <ul>
        <li>Fast processing</li>
        <li>AI-powered</li>
        <li>Easy to use</li>
    </ul>
    
    <h2>Steps:</h2>
    <ol>
        <li>Install the software</li>
        <li>Configure settings</li>
        <li>Start using</li>
    </ol>
    """
    
    result = await extract_lists(content=html)
    
    assert result["success"] is True
    assert result["lists_found"] == 2
    assert result["total_items"] == 6


@pytest.mark.asyncio
async def test_extract_metadata():
    """Test metadata extraction"""
    html = """
    <head>
        <title>Test Page</title>
        <meta name="description" content="This is a test page">
        <meta property="og:title" content="Test OG Title">
        <meta property="og:image" content="https://example.com/image.jpg">
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "WebPage", "name": "Test"}
        </script>
    </head>
    """
    
    result = await extract_metadata(html_content=html)
    
    assert result["success"] is True
    assert "basic" in result["metadata"]
    assert result["metadata"]["basic"]["title"] == "Test Page"
    assert "opengraph" in result["metadata"]
    assert result["metadata"]["opengraph"]["title"] == "Test OG Title"
    assert "jsonld" in result["metadata"]


@pytest.mark.asyncio
async def test_extract_patterns():
    """Test pattern extraction"""
    content = """
    Order #12345 placed on 2024-06-28 for $199.99
    Order #67890 placed on 2024-06-29 for $299.99
    """
    
    result = await extract_patterns(
        content=content,
        patterns={
            "order_ids": r"#(\d{5})",
            "dates": r"\d{4}-\d{2}-\d{2}",
            "prices": r"\$\d+\.\d{2}"
        }
    )
    
    assert result["success"] is True
    assert len(result["extracted"]["order_ids"]) == 2
    assert "12345" in result["extracted"]["order_ids"]
    assert len(result["extracted"]["prices"]) == 2
    assert "$199.99" in result["extracted"]["prices"]


@pytest.mark.asyncio
async def test_extract_by_proximity():
    """Test proximity-based extraction"""
    content = """
    Product Name: iPhone 15 Pro Max
    Price: $1,199
    Stock: 25 units
    Color: Space Black
    """
    
    result = await extract_by_proximity(
        content=content,
        keywords=["Product Name", "Price", "Stock", "Color"],
        proximity_chars=30
    )
    
    assert result["success"] is True
    assert result["extracted"]["Price"] == "$1,199"
    assert result["extracted"]["Stock"] == "25 units"
    assert result["extracted"]["Color"] == "Space Black"


@pytest.mark.asyncio
async def test_extractor_tool_registration():
    """Test that all extractor tools are properly registered"""
    from ai_core.registry import tool_registry
    
    tools = tool_registry.list_tools()
    
    # Check that extractor tools are registered
    extractor_tools = [
        "extract_structured_data",
        "extract_tables",
        "extract_contact_info",
        "extract_lists",
        "extract_metadata",
        "extract_patterns",
        "extract_by_proximity"
    ]
    
    for tool_name in extractor_tools:
        assert tool_name in tools, f"Tool {tool_name} not registered"


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_extract_structured_data())
    asyncio.run(test_extract_tables())
    asyncio.run(test_extract_contact_info())
    asyncio.run(test_extract_lists())
    asyncio.run(test_extract_metadata())
    asyncio.run(test_extract_patterns())
    asyncio.run(test_extract_by_proximity())
    asyncio.run(test_extractor_tool_registration())
    
    print("✅ All ExtractorTool tests passed!")
