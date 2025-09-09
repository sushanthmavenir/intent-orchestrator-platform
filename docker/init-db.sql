-- Intent Orchestration Platform Database Initialization
-- PostgreSQL database setup for production deployment

-- Create database if not exists (handled by docker-compose environment)
-- CREATE DATABASE IF NOT EXISTS intent_orchestrator;

-- Create main tables for TMF 921A Intent Management

-- Intents table
CREATE TABLE IF NOT EXISTS intents (
    id VARCHAR(255) PRIMARY KEY,
    href VARCHAR(500),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    expression TEXT,
    expression_language VARCHAR(50) DEFAULT 'SIMPLE',
    lifecycle_status VARCHAR(50) DEFAULT 'IN_STUDY',
    priority INTEGER DEFAULT 5,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    characteristics JSONB,
    applicable_time_period JSONB,
    place JSONB,
    intent_type VARCHAR(50) DEFAULT 'customer_intent',
    engagement_type VARCHAR(50),
    expected_fulfillment_date TIMESTAMP,
    related_intent JSONB,
    business_relevance_score REAL DEFAULT 0.5,
    fulfillment_information JSONB
);

-- Intent reports table
CREATE TABLE IF NOT EXISTS intent_reports (
    id VARCHAR(255) PRIMARY KEY,
    intent_id VARCHAR(255) NOT NULL,
    href VARCHAR(500),
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_type VARCHAR(100) DEFAULT 'progress',
    status VARCHAR(50) DEFAULT 'in_progress',
    description TEXT,
    characteristics JSONB,
    applicable_time_period JSONB,
    place JSONB,
    related_intent JSONB,
    FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE CASCADE
);

-- Event subscriptions table
CREATE TABLE IF NOT EXISTS event_subscriptions (
    id VARCHAR(255) PRIMARY KEY,
    callback_url VARCHAR(500) NOT NULL,
    query_params JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Agent registry table for MCP agents
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    capabilities JSONB,
    status VARCHAR(50) DEFAULT 'available',
    endpoint_url VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP,
    performance_metrics JSONB
);

-- Workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id VARCHAR(255) PRIMARY KEY,
    workflow_type VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    agent_executions JSONB,
    error_details JSONB
);

-- Intent analysis results table
CREATE TABLE IF NOT EXISTS intent_analysis (
    id VARCHAR(255) PRIMARY KEY,
    intent_id VARCHAR(255),
    analysis_type VARCHAR(100) NOT NULL,
    input_text TEXT,
    classification_result JSONB,
    confidence_score REAL,
    entities_extracted JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,
    FOREIGN KEY (intent_id) REFERENCES intents(id) ON DELETE SET NULL
);

-- Fraud detection cases table
CREATE TABLE IF NOT EXISTS fraud_cases (
    id VARCHAR(255) PRIMARY KEY,
    customer_phone VARCHAR(50),
    caller_phone VARCHAR(50),
    case_type VARCHAR(100) DEFAULT 'social_engineering',
    risk_score REAL DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'LOW',
    status VARCHAR(50) DEFAULT 'open',
    details JSONB,
    agent_analysis JSONB,
    recommendations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_intents_lifecycle_status ON intents(lifecycle_status);
CREATE INDEX IF NOT EXISTS idx_intents_category ON intents(category);
CREATE INDEX IF NOT EXISTS idx_intents_creation_date ON intents(creation_date);
CREATE INDEX IF NOT EXISTS idx_intents_priority ON intents(priority);

CREATE INDEX IF NOT EXISTS idx_intent_reports_intent_id ON intent_reports(intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_reports_creation_date ON intent_reports(creation_date);
CREATE INDEX IF NOT EXISTS idx_intent_reports_status ON intent_reports(status);

CREATE INDEX IF NOT EXISTS idx_agent_registry_status ON agent_registry(status);
CREATE INDEX IF NOT EXISTS idx_agent_registry_last_heartbeat ON agent_registry(last_heartbeat);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_started_at ON workflow_executions(started_at);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_type ON workflow_executions(workflow_type);

CREATE INDEX IF NOT EXISTS idx_intent_analysis_intent_id ON intent_analysis(intent_id);
CREATE INDEX IF NOT EXISTS idx_intent_analysis_analysis_type ON intent_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_intent_analysis_created_at ON intent_analysis(created_at);

CREATE INDEX IF NOT EXISTS idx_fraud_cases_customer_phone ON fraud_cases(customer_phone);
CREATE INDEX IF NOT EXISTS idx_fraud_cases_risk_level ON fraud_cases(risk_level);
CREATE INDEX IF NOT EXISTS idx_fraud_cases_status ON fraud_cases(status);
CREATE INDEX IF NOT EXISTS idx_fraud_cases_created_at ON fraud_cases(created_at);

-- Insert sample data for testing
INSERT INTO intents (id, name, description, expression, category, priority)
VALUES 
    ('intent-001', 'Customer Verification Request', 'Intent to verify customer identity', 'verify customer identity', 'security', 1),
    ('intent-002', 'Fraud Detection Alert', 'Intent to detect and prevent fraudulent activity', 'detect fraud patterns', 'security', 1),
    ('intent-003', 'Service Quality Inquiry', 'Intent to inquire about service quality metrics', 'check service quality', 'customer_service', 3)
ON CONFLICT (id) DO NOTHING;

-- Create function to update last_update timestamp
CREATE OR REPLACE FUNCTION update_last_update_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_update = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for intents table
CREATE TRIGGER update_intents_last_update
    BEFORE UPDATE ON intents
    FOR EACH ROW
    EXECUTE FUNCTION update_last_update_column();

-- Create function to update updated_at timestamp for fraud_cases
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for fraud_cases table
CREATE TRIGGER update_fraud_cases_updated_at
    BEFORE UPDATE ON fraud_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO intent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO intent_user;

-- Create views for common queries
CREATE OR REPLACE VIEW active_intents AS
SELECT * FROM intents 
WHERE lifecycle_status IN ('FEASIBILITY_CHECKED', 'DESIGNED', 'IMPLEMENTED', 'DEPLOYED');

CREATE OR REPLACE VIEW high_priority_intents AS
SELECT * FROM intents 
WHERE priority <= 2 
ORDER BY priority ASC, creation_date ASC;

CREATE OR REPLACE VIEW recent_fraud_cases AS
SELECT * FROM fraud_cases 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW agent_health_summary AS
SELECT 
    agent_id,
    name,
    status,
    last_heartbeat,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat))/60 as minutes_since_heartbeat,
    (metadata->>'version') as version
FROM agent_registry
ORDER BY last_heartbeat DESC;

-- Insert initial system configurations
INSERT INTO agent_registry (agent_id, name, description, capabilities, status)
VALUES 
    ('fraud_detection_agent', 'Fraud Detection Agent', 'Comprehensive fraud detection using multiple CAMARA APIs', '["comprehensive_fraud_detection", "risk_assessment", "pattern_analysis"]', 'available'),
    ('sim_swap_agent', 'SIM Swap Detection Agent', 'Specialized agent for detecting SIM swap fraud', '["sim_swap_detection", "sim_history_analysis", "fraud_risk_assessment"]', 'available'),
    ('kyc_match_agent', 'KYC Match Verification Agent', 'Identity verification using CAMARA KYC Match API', '["identity_verification", "document_validation", "compliance_check"]', 'available'),
    ('device_location_agent', 'Device Location Analysis Agent', 'Device location tracking and geospatial analysis', '["location_verification", "movement_analysis", "geofencing", "location_risk_assessment"]', 'available'),
    ('scam_signal_agent', 'Scam Signal Detection Agent', 'Social engineering and scam detection', '["scam_detection", "social_engineering_analysis", "communication_pattern_analysis", "threat_assessment"]', 'available')
ON CONFLICT (agent_id) DO NOTHING;

COMMIT;