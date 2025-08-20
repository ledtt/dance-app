-- Database initialization script for Dance App
-- This script sets up the database with proper permissions and indexes

-- Create database if it doesn't exist
-- (PostgreSQL will create it automatically based on POSTGRES_DB environment variable)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Create schemas for different services
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS schedule;
CREATE SCHEMA IF NOT EXISTS booking;

-- Grant permissions
GRANT USAGE ON SCHEMA auth TO postgres;
GRANT USAGE ON SCHEMA schedule TO postgres;
GRANT USAGE ON SCHEMA booking TO postgres;

-- Create users table in auth schema
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(320) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON auth.users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON auth.users(created_at);

-- Create class_templates table in schedule schema
CREATE TABLE IF NOT EXISTS schedule.class_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    teacher VARCHAR(100) NOT NULL,
    weekday INTEGER NOT NULL CHECK (weekday >= 1 AND weekday <= 7),
    start_time TIME NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0 AND capacity <= 100),
    comment TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for class_templates table
CREATE INDEX IF NOT EXISTS idx_class_templates_weekday ON schedule.class_templates(weekday);
CREATE INDEX IF NOT EXISTS idx_class_templates_teacher ON schedule.class_templates(teacher);
CREATE INDEX IF NOT EXISTS idx_class_templates_active ON schedule.class_templates(active);
CREATE INDEX IF NOT EXISTS idx_class_templates_created_at ON schedule.class_templates(created_at);

-- Create bookings table in booking schema
CREATE TABLE IF NOT EXISTS booking.bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    class_id UUID NOT NULL,
    date DATE NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for bookings table
CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON booking.bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_class_id ON booking.bookings(class_id);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON booking.bookings(date);
CREATE INDEX IF NOT EXISTS idx_bookings_start_time ON booking.bookings(start_time);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON booking.bookings(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_user_class_date ON booking.bookings(user_id, class_id, date);

-- Grant permissions on tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA schedule TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA booking TO postgres;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA schedule TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA booking TO postgres;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON auth.users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_class_templates_updated_at 
    BEFORE UPDATE ON schedule.class_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for analytics
CREATE OR REPLACE VIEW booking.booking_stats AS
SELECT 
    COUNT(*) as total_bookings,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT class_id) as unique_classes,
    DATE_TRUNC('day', created_at) as booking_date
FROM booking.bookings
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY booking_date DESC;

-- Grant permissions on views
GRANT SELECT ON ALL TABLES IN SCHEMA booking TO postgres;

-- Create function for cleaning old bookings (for maintenance)
CREATE OR REPLACE FUNCTION booking.cleanup_old_bookings(days_old INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM booking.bookings 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_old;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission on cleanup function
GRANT EXECUTE ON FUNCTION booking.cleanup_old_bookings(INTEGER) TO postgres;

-- Set search path for the application
ALTER DATABASE dance_app SET search_path TO auth, schedule, booking, public; 