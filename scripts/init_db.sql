-- Database initialization script for Intelligent Crawl4AI Agent
-- This script sets up the database schema for high-volume scraping operations

-- Create database (this is handled by Docker environment variables)
-- CREATE DATABASE intelligent_scraping;

-- Create tables for high-volume job management
CREATE TABLE IF NOT EXISTS high_volume_jobs (
    job_id VARCHAR PRIMARY KEY,
    urls_count INTEGER NOT NULL,
    purpose VARCHAR NOT NULL,
    priority INTEGER DEFAULT 1,
    batch_size INTEGER DEFAULT 100,
    max_workers INTEGER DEFAULT 50,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    progress JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Create table for individual URL processing results
CREATE TABLE IF NOT EXISTS url_results (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    success BOOLEAN NOT NULL,
    extracted_data JSONB,
    error_message TEXT,
    processing_time FLOAT,
    strategy_used VARCHAR,
    worker_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    FOREIGN KEY (job_id) REFERENCES high_volume_jobs(job_id)
);

-- Create table for worker statistics
CREATE TABLE IF NOT EXISTS worker_stats (
    worker_id VARCHAR PRIMARY KEY,
    urls_processed INTEGER DEFAULT 0,
    successful_extractions INTEGER DEFAULT 0,
    failed_extractions INTEGER DEFAULT 0,
    current_job_id VARCHAR,
    last_activity TIMESTAMP DEFAULT NOW(),
    status VARCHAR DEFAULT 'idle'
);

-- Create table for strategy learning and optimization
CREATE TABLE IF NOT EXISTS strategy_learning (
    id SERIAL PRIMARY KEY,
    url VARCHAR NOT NULL,
    website_type VARCHAR NOT NULL,
    purpose VARCHAR NOT NULL,
    strategy_used VARCHAR NOT NULL,
    success_rate FLOAT NOT NULL,
    extraction_config JSONB,
    analysis_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create table for CSS selector learning
CREATE TABLE IF NOT EXISTS selector_learning (
    id SERIAL PRIMARY KEY,
    website_type VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    css_selector VARCHAR NOT NULL,
    success_rate FLOAT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicates
    UNIQUE(website_type, content_type, css_selector)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_url_results_job_id ON url_results(job_id);
CREATE INDEX IF NOT EXISTS idx_url_results_success ON url_results(success);
CREATE INDEX IF NOT EXISTS idx_url_results_created_at ON url_results(created_at);
CREATE INDEX IF NOT EXISTS idx_worker_stats_status ON worker_stats(status);
CREATE INDEX IF NOT EXISTS idx_strategy_learning_website_type ON strategy_learning(website_type);
CREATE INDEX IF NOT EXISTS idx_strategy_learning_purpose ON strategy_learning(purpose);
CREATE INDEX IF NOT EXISTS idx_selector_learning_website_type ON selector_learning(website_type);

-- Create views for common queries
CREATE OR REPLACE VIEW job_summary AS
SELECT 
    hj.job_id,
    hj.purpose,
    hj.status,
    hj.urls_count as total_urls,
    hj.created_at,
    hj.started_at,
    hj.completed_at,
    COUNT(ur.id) as processed_urls,
    SUM(CASE WHEN ur.success THEN 1 ELSE 0 END) as successful_urls,
    SUM(CASE WHEN NOT ur.success THEN 1 ELSE 0 END) as failed_urls,
    AVG(ur.processing_time) as avg_processing_time,
    CASE 
        WHEN hj.urls_count > 0 THEN 
            ROUND((COUNT(ur.id)::FLOAT / hj.urls_count * 100), 2)
        ELSE 0 
    END as completion_percentage
FROM high_volume_jobs hj
LEFT JOIN url_results ur ON hj.job_id = ur.job_id
GROUP BY hj.job_id, hj.purpose, hj.status, hj.urls_count, hj.created_at, hj.started_at, hj.completed_at;

-- Create view for worker performance
CREATE OR REPLACE VIEW worker_performance AS
SELECT 
    ws.worker_id,
    ws.status,
    ws.urls_processed,
    ws.successful_extractions,
    ws.failed_extractions,
    CASE 
        WHEN ws.urls_processed > 0 THEN 
            ROUND((ws.successful_extractions::FLOAT / ws.urls_processed * 100), 2)
        ELSE 0 
    END as success_rate,
    ws.current_job_id,
    ws.last_activity,
    COUNT(ur.id) as recent_urls_processed
FROM worker_stats ws
LEFT JOIN url_results ur ON ws.worker_id = ur.worker_id 
    AND ur.created_at > NOW() - INTERVAL '1 hour'
GROUP BY ws.worker_id, ws.status, ws.urls_processed, ws.successful_extractions, 
         ws.failed_extractions, ws.current_job_id, ws.last_activity;

-- Create view for strategy effectiveness
CREATE OR REPLACE VIEW strategy_effectiveness AS
SELECT 
    sl.website_type,
    sl.purpose,
    sl.strategy_used,
    COUNT(*) as usage_count,
    AVG(sl.success_rate) as avg_success_rate,
    MIN(sl.success_rate) as min_success_rate,
    MAX(sl.success_rate) as max_success_rate,
    MAX(sl.created_at) as last_used
FROM strategy_learning sl
GROUP BY sl.website_type, sl.purpose, sl.strategy_used
ORDER BY avg_success_rate DESC, usage_count DESC;

-- Insert some default data for testing
INSERT INTO worker_stats (worker_id, status) 
VALUES 
    ('worker_0', 'idle'),
    ('worker_1', 'idle'),
    ('worker_2', 'idle')
ON CONFLICT (worker_id) DO NOTHING;

-- Create function to clean old data (optional maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Delete URL results older than 30 days
    DELETE FROM url_results 
    WHERE created_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete completed jobs older than 90 days
    DELETE FROM high_volume_jobs 
    WHERE status = 'completed' 
    AND completed_at < NOW() - INTERVAL '90 days';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your security requirements)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scraper_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scraper_user;

-- Log successful initialization
INSERT INTO high_volume_jobs (job_id, urls_count, purpose, status, metadata)
VALUES (
    'init_' || EXTRACT(EPOCH FROM NOW())::TEXT,
    0,
    'database_initialization',
    'completed',
    '{"message": "Database schema initialized successfully", "version": "1.0"}'::JSONB
);

-- Display initialization summary
SELECT 
    'Database initialization completed successfully' as status,
    COUNT(*) as tables_created
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'high_volume_jobs', 
    'url_results', 
    'worker_stats', 
    'strategy_learning', 
    'selector_learning'
);
