-- ============================================
-- StormGuard Database Migration - Airflow Integration
-- ============================================
-- Add alert metrics table for monitoring

-- Create alert_metrics table for tracking alert sends
CREATE TABLE IF NOT EXISTS alert_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    total_sent INT DEFAULT 0,
    total_failed INT DEFAULT 0,
    errors TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_metric_timestamp UNIQUE (timestamp)
);

-- Create index for time-series queries
CREATE INDEX IF NOT EXISTS idx_alert_metrics_timestamp 
ON alert_metrics(timestamp DESC);

-- Create predictions table (if not exists - adjust schema as needed)
-- This is referenced by the alert trigger DAG
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    prediction_id UUID UNIQUE,
    disaster_type VARCHAR(50) NOT NULL,
    risk_score DECIMAL(3, 2) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    affected_radius_km INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at 
ON predictions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_risk_score 
ON predictions(risk_score DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_disaster_type 
ON predictions(disaster_type);

-- Create view for daily alert summary
CREATE OR REPLACE VIEW daily_alert_summary AS
SELECT 
    DATE(timestamp) as alert_date,
    SUM(total_sent) as total_alerts_sent,
    SUM(total_failed) as total_alerts_failed,
    COUNT(*) as trigger_counts,
    MAX(timestamp) as last_trigger
FROM alert_metrics
GROUP BY DATE(timestamp)
ORDER BY alert_date DESC;

-- Create view for alert success rate
CREATE OR REPLACE VIEW alert_success_rate AS
SELECT 
    CASE 
        WHEN SUM(total_sent) + SUM(total_failed) = 0 THEN 0
        ELSE (SUM(total_sent)::FLOAT / (SUM(total_sent) + SUM(total_failed))) * 100
    END as success_rate_percent,
    SUM(total_sent) as total_sent,
    SUM(total_failed) as total_failed,
    COUNT(*) as trigger_count
FROM alert_metrics
WHERE timestamp >= NOW() - INTERVAL '7 days';

-- If disaster types are tracked separately, create this table:
CREATE TABLE IF NOT EXISTS alert_metrics_by_type (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    disaster_type VARCHAR(50) NOT NULL,
    alerts_sent INT DEFAULT 0,
    alerts_failed INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_metrics_by_type_timestamp 
ON alert_metrics_by_type(timestamp DESC, disaster_type);
