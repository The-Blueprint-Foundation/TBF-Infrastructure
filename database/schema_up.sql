-- Build up script for the sensor monitoring schema
-- pgcrypto extension for gen_random_uuid()
-- All objects live in a dedicated schema

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS air_quality;

CREATE TABLE air_quality.locations (
    location_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    latitude      DECIMAL(9, 6) NOT NULL,
    longitude     DECIMAL(9, 6) NOT NULL,
    neighborhood  VARCHAR(255)
);

CREATE TABLE air_quality.sensors (
    sensor_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id   UUID NOT NULL REFERENCES air_quality.locations(location_id),
    name          VARCHAR(255) NOT NULL,
    status        VARCHAR(50) NOT NULL DEFAULT 'active',
    extrnl_id     VARCHAR(255),
    extrnl_source VARCHAR(100),
    UNIQUE (extrnl_source, extrnl_id)
);

-- Explicit measurement columns
-- Units are fixed per column rather than per row.
CREATE TABLE air_quality.sensor_readings (
    reading_id     BIGSERIAL PRIMARY KEY,
    sensor_id      UUID NOT NULL REFERENCES air_quality.sensors(sensor_id),
    recorded_at    TIMESTAMPTZ NOT NULL,
    pm1_0          DECIMAL(8, 2),   -- PM1.0, ug/m^3
    pm2_5          DECIMAL(8, 2),   -- PM2.5, ug/m^3
    pm10           DECIMAL(8, 2),   -- PM10, ug/m^3
    temperature    DECIMAL(6, 2),   -- degrees celsius
    humidity       DECIMAL(5, 2),   -- relative humidity, %
    pressure       DECIMAL(7, 2),   -- barometric pressure, hpa
    quality_flag   VARCHAR(50)
);

-- Helpful indexes for common lookups
CREATE INDEX idx_sensors_location_id ON air_quality.sensors(location_id);
CREATE INDEX idx_sensor_readings_sensor_id ON air_quality.sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_recorded_at ON air_quality.sensor_readings(recorded_at);
