-- ============================================
-- StormGuard Database Migration - Phase 1
-- ============================================
-- Create user management tables

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    city VARCHAR(255),
    country VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    interests TEXT,
    notification_enabled BOOLEAN DEFAULT true,
    notification_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    CONSTRAINT users_email_unique UNIQUE (email)
);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY,
    hurricane_alerts BOOLEAN DEFAULT true,
    heat_wave_alerts BOOLEAN DEFAULT true,
    flood_alerts BOOLEAN DEFAULT true,
    severe_storm_alerts BOOLEAN DEFAULT true,
    min_risk_level VARCHAR(50) DEFAULT 'MEDIUM',
    alert_radius_km INT DEFAULT 100,
    max_daily_alerts INT DEFAULT 10,
    quiet_hours_start VARCHAR(10),
    quiet_hours_end VARCHAR(10),
    enable_push BOOLEAN DEFAULT true,
    enable_email BOOLEAN DEFAULT false,
    enable_sms BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_pref FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    disaster_type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    message TEXT,
    risk_level VARCHAR(50),
    risk_score DECIMAL(3, 2),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    radius_km INT,
    sent BOOLEAN DEFAULT false,
    read BOOLEAN DEFAULT false,
    clicked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    CONSTRAINT fk_alert_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT,
    sources JSON,
    session_id VARCHAR(255),
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_location ON users(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_disaster_type ON alerts(disaster_type);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_created_at ON chat_messages(created_at);

-- Create updated_at trigger for users table
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at_trigger
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_users_updated_at();

-- Create updated_at trigger for user_preferences table
CREATE OR REPLACE FUNCTION update_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER preferences_updated_at_trigger
BEFORE UPDATE ON user_preferences
FOR EACH ROW
EXECUTE FUNCTION update_preferences_updated_at();
