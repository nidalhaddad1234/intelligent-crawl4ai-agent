#!/usr/bin/env python3
"""
Model Setup Script for Intelligent Crawl4AI Agent
Automatically downloads and configures DeepSeek models for web scraping
"""

import os
import sys
import time
import requests
import subprocess
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
MODELS_TO_DOWNLOAD = [
    {
        'name': 'deepseek-coder:1.3b',
        'description': 'DeepSeek Coder 1.3B - Optimized for web scraping',
        'priority': 1
    },
    {
        'name': 'nomic-embed-text:latest',
        'description': 'Nomic Embeddings - For vector search',
        'priority': 2
    },
    {
        'name': 'llama3.1:latest',
        'description': 'Llama 3.1 - Fallback model',
        'priority': 3
    }
]

def wait_for_ollama(max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for Ollama service to be ready"""
    logger.info(f"Waiting for Ollama at {OLLAMA_URL}...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama is ready!")
                return True
        except requests.RequestException as e:
            if attempt == 0:
                logger.info(f"⏳ Ollama not ready yet, waiting... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    logger.error("❌ Ollama failed to become ready")
    return False

def check_model_exists(model_name: str) -> bool:
    """Check if a model already exists in Ollama"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            existing_models = [model['name'] for model in models_data.get('models', [])]
            return model_name in existing_models
    except Exception as e:
        logger.warning(f"Could not check existing models: {e}")
        return False

def download_model(model_info: Dict) -> bool:
    """Download a model using Ollama"""
    model_name = model_info['name']
    description = model_info['description']
    
    logger.info(f"📥 Downloading {model_name} - {description}")
    
    try:
        # Use ollama pull command
        result = subprocess.run(
            ['ollama', 'pull', model_name],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully downloaded {model_name}")
            return True
        else:
            logger.error(f"❌ Failed to download {model_name}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout downloading {model_name}")
        return False
    except Exception as e:
        logger.error(f"❌ Error downloading {model_name}: {e}")
        return False

def test_model(model_name: str) -> bool:
    """Test if a model is working correctly"""
    logger.info(f"🧪 Testing {model_name}...")
    
    try:
        test_prompt = "Analyze this HTML: <div class='price'>$99.99</div>"
        
        result = subprocess.run(
            ['ollama', 'run', model_name, test_prompt],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and len(result.stdout.strip()) > 0:
            logger.info(f"✅ {model_name} is working correctly")
            return True
        else:
            logger.warning(f"⚠️ {model_name} test failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Could not test {model_name}: {e}")
        return False

def set_primary_model(model_name: str) -> bool:
    """Set the primary model for the crawler"""
    logger.info(f"🎯 Setting {model_name} as primary model...")
    
    # Create environment variable for services
    env_content = f"""
# Primary AI Model Configuration
OLLAMA_PRIMARY_MODEL={model_name}
OLLAMA_MODEL={model_name}

# Model Performance Settings
OLLAMA_FLASH_ATTENTION=1
OLLAMA_NUM_PARALLEL=4
OLLAMA_MAX_LOADED_MODELS=2
"""
    
    try:
        with open('/app/config/model_config.env', 'w') as f:
            f.write(env_content)
        logger.info(f"✅ Primary model set to {model_name}")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Could not set primary model config: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 Starting Intelligent Crawl4AI Model Setup")
    logger.info("=" * 60)
    
    # Wait for Ollama to be ready
    if not wait_for_ollama():
        logger.error("❌ Ollama service is not available. Exiting.")
        sys.exit(1)
    
    # Sort models by priority
    models_to_process = sorted(MODELS_TO_DOWNLOAD, key=lambda x: x['priority'])
    
    downloaded_models = []
    primary_model = None
    
    # Download models
    for model_info in models_to_process:
        model_name = model_info['name']
        
        # Check if model already exists
        if check_model_exists(model_name):
            logger.info(f"✅ {model_name} already exists, skipping download")
            downloaded_models.append(model_name)
            if not primary_model and 'deepseek' in model_name:
                primary_model = model_name
            continue
        
        # Download the model
        if download_model(model_info):
            downloaded_models.append(model_name)
            if not primary_model and 'deepseek' in model_name:
                primary_model = model_name
        else:
            logger.warning(f"⚠️ Skipping {model_name} due to download failure")
    
    # Test primary model
    if primary_model:
        test_model(primary_model)
        set_primary_model(primary_model)
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 SETUP SUMMARY")
    logger.info(f"✅ Downloaded models: {len(downloaded_models)}")
    for model in downloaded_models:
        logger.info(f"   - {model}")
    
    if primary_model:
        logger.info(f"🎯 Primary model: {primary_model}")
        logger.info("🚀 Ready for intelligent web scraping!")
    else:
        logger.warning("⚠️ No DeepSeek model available. Using fallback.")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
