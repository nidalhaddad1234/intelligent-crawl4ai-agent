-- Initialize database for AI-First Web Scraping Agent
-- This script sets up the core tables for all 8 features

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Feature 1-3: Sessions and conversations
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_context JSONB DEFAULT '{}',
    total_messages INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature 2: Intent analysis
CREATE TABLE IF NOT EXISTS intent_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    message_id UUID REFERENCES chat_messages(id),
    primary_intent VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    parameters JSONB DEFAULT '{}',
    targets TEXT[] DEFAULT '{}',
    needs_clarification BOOLEAN DEFAULT FALSE,
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature 4: Background jobs
CREATE TABLE IF NOT EXISTS background_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    description TEXT,
    target_url TEXT,
    parameters JSONB DEFAULT '{}',
    progress FLOAT DEFAULT 0.0,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_duration INTEGER
);

-- Feature 5: Learning and patterns
CREATE TABLE IF NOT EXISTS successful_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id VARCHAR(255) UNIQUE NOT NULL,
    request_text TEXT NOT NULL,
    intent_analysis JSONB NOT NULL,
    execution_config JSONB NOT NULL,
    success_metrics JSONB DEFAULT '{}',
    user_feedback TEXT,
    reuse_count INTEGER DEFAULT 0,
    success_score FLOAT NOT NULL,
    context_tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pattern_embeddings (
    pattern_id VARCHAR(255) REFERENCES successful_patterns(pattern_id),
    embedding FLOAT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (pattern_id)
);

-- Feature 6: Tool selection and performance
CREATE TABLE IF NOT EXISTS tool_selections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    primary_tool VARCHAR(100) NOT NULL,
    alternative_tools TEXT[] DEFAULT '{}',
    strategy VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    reasoning TEXT,
    configuration JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tool_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tool_name VARCHAR(100) NOT NULL,
    execution_time FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature 7: Progress tracking
CREATE TABLE IF NOT EXISTS progress_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    task_id VARCHAR(255) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    progress FLOAT DEFAULT 0.0,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature 8: Schema detection and content analysis
CREATE TABLE IF NOT EXISTS page_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id VARCHAR(255) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    schemas_found INTEGER DEFAULT 0,
    patterns_found INTEGER DEFAULT 0,
    rules_generated INTEGER DEFAULT 0,
    analysis_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS detected_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_id VARCHAR(255) UNIQUE NOT NULL,
    analysis_id VARCHAR(255) REFERENCES page_analyses(analysis_id),
    schema_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    selector_path TEXT NOT NULL,
    xpath_path TEXT,
    element_count INTEGER DEFAULT 0,
    schema_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id VARCHAR(255) UNIQUE NOT NULL,
    analysis_id VARCHAR(255) REFERENCES page_analyses(analysis_id),
    pattern_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    repeat_count INTEGER DEFAULT 0,
    consistency_score FLOAT DEFAULT 0.0,
    css_selector TEXT,
    xpath TEXT,
    pattern_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS extraction_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(255) UNIQUE NOT NULL,
    analysis_id VARCHAR(255) REFERENCES page_analyses(analysis_id),
    target_selector TEXT NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    extraction_method VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    validation_rules TEXT[] DEFAULT '{}',
    transformation_rules TEXT[] DEFAULT '{}',
    fallback_selectors TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_background_jobs_session_id ON background_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_successful_patterns_context_tags ON successful_patterns USING GIN(context_tags);
CREATE INDEX IF NOT EXISTS idx_tool_performance_tool_name ON tool_performance(tool_name);
CREATE INDEX IF NOT EXISTS idx_page_analyses_url ON page_analyses(url);
CREATE INDEX IF NOT EXISTS idx_detected_schemas_analysis_id ON detected_schemas(analysis_id);
CREATE INDEX IF NOT EXISTS idx_content_patterns_analysis_id ON content_patterns(analysis_id);
CREATE INDEX IF NOT EXISTS idx_extraction_rules_analysis_id ON extraction_rules(analysis_id);

-- Create views for analytics
CREATE OR REPLACE VIEW session_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_sessions,
    AVG(total_messages) as avg_messages_per_session,
    AVG(success_rate) as avg_success_rate
FROM chat_sessions 
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

CREATE OR REPLACE VIEW tool_performance_analytics AS
SELECT 
    tool_name,
    COUNT(*) as total_executions,
    AVG(execution_time) as avg_execution_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,
    DATE_TRUNC('day', created_at) as date
FROM tool_performance 
GROUP BY tool_name, DATE_TRUNC('day', created_at)
ORDER BY date DESC, tool_name;

CREATE OR REPLACE VIEW content_analysis_stats AS
SELECT 
    content_type,
    COUNT(*) as total_analyses,
    AVG(confidence) as avg_confidence,
    AVG(schemas_found) as avg_schemas_found,
    AVG(patterns_found) as avg_patterns_found,
    AVG(rules_generated) as avg_rules_generated
FROM page_analyses 
GROUP BY content_type
ORDER BY total_analyses DESC;

-- Insert some initial data
INSERT INTO chat_sessions (session_id, user_context) VALUES 
('demo-session', '{"user_type": "demo", "preferences": {"theme": "dark"}}')
ON CONFLICT (session_id) DO NOTHING;

-- Set up permissions for the scraper user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scraper;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scraper;
GRANT USAGE ON SCHEMA public TO scraper;

-- Create stored procedure for cleaning old data
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old chat messages (keep last 30 days)
    DELETE FROM chat_messages WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old background jobs
    DELETE FROM background_jobs WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old progress events
    DELETE FROM progress_events WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old tool performance records
    DELETE FROM tool_performance WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get system health
CREATE OR REPLACE FUNCTION get_system_health()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'active_sessions', (SELECT COUNT(*) FROM chat_sessions WHERE last_activity > NOW() - INTERVAL '1 hour'),
        'total_messages_today', (SELECT COUNT(*) FROM chat_messages WHERE created_at > CURRENT_DATE),
        'running_jobs', (SELECT COUNT(*) FROM background_jobs WHERE status = 'running'),
        'successful_patterns', (SELECT COUNT(*) FROM successful_patterns),
        'total_analyses', (SELECT COUNT(*) FROM page_analyses WHERE created_at > CURRENT_DATE),
        'avg_confidence', (SELECT AVG(confidence) FROM page_analyses WHERE created_at > CURRENT_DATE),
        'system_uptime', EXTRACT(EPOCH FROM (NOW() - (SELECT MIN(created_at) FROM chat_sessions)))
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMIT;
