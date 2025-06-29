-- Initial database setup for Intelligent Crawl4AI
-- This file is automatically run when PostgreSQL starts

-- Create tables for extraction jobs
CREATE TABLE IF NOT EXISTS extraction_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    urls TEXT[],
    purpose VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    batch_size INTEGER DEFAULT 100,
    max_workers INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create table for extracted data
CREATE TABLE IF NOT EXISTS extracted_data (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) REFERENCES extraction_jobs(job_id),
    url TEXT NOT NULL,
    purpose VARCHAR(255),
    strategy_used VARCHAR(100),
    data JSONB,
    raw_html TEXT,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    extraction_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_job_id ON extracted_data(job_id);
CREATE INDEX IF NOT EXISTS idx_url ON extracted_data(url);
CREATE INDEX IF NOT EXISTS idx_success ON extracted_data(success);
CREATE INDEX IF NOT EXISTS idx_created_at ON extracted_data(created_at);

-- Create table for strategy performance tracking
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100),
    website_type VARCHAR(100),
    success_rate FLOAT,
    avg_extraction_time FLOAT,
    total_uses INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scraper_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scraper_user;
