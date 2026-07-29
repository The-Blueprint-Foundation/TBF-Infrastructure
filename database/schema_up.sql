-- Build up script for the sensor monitoring schema
-- 3 tables: LOCATIONS to SENSORS to SENSOR_READINGS
-- Requires the pgcrypto extension for gen_random_uuid()

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE locations (
    location_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    latitude      DECIMAL(9, 6) NOT NULL,
    longitude     DECIMAL(9, 6) NOT NULL,
    neighborhood  VARCHAR(255),
    indoor        BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE sensors (
    sensor_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id   UUID NOT NULL REFERENCES locations(location_id),
    name          VARCHAR(255) NOT NULL,
    status        VARCHAR(50) NOT NULL DEFAULT 'active'
);

CREATE TABLE sensor_readings (
    reading_id        BIGSERIAL PRIMARY KEY,
    sensor_id         UUID NOT NULL REFERENCES sensors(sensor_id),
    measurement_type  VARCHAR(100) NOT NULL,
    unit              VARCHAR(50) NOT NULL,
    value             DECIMAL(12, 4) NOT NULL,
    recorded_at       TIMESTAMPTZ NOT NULL,
    quality_flag      VARCHAR(50)
);

-- Helpful indexes for common lookups
CREATE INDEX idx_sensors_location_id ON sensors(location_id);
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_recorded_at ON sensor_readings(recorded_at);
