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
    neighborhood  VARCHAR(255),
    UNIQUE (name, latitude, longitude)
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

-- Stored Procedure to facilitate ingesting data from sensors
CREATE OR REPLACE PROCEDURE air_quality.submit_readings (
  p_extrnl_id VARCHAR,
  p_extrnl_source VARCHAR,
  p_name VARCHAR,
  p_long NUMERIC,
  p_lat NUMERIC,
  p_pm1_0 NUMERIC,
  p_pm2_5 NUMERIC,
  p_pm10 NUMERIC,
  p_temperature NUMERIC,
  p_pressure NUMERIC,
  p_humidity NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_location_id uuid;
    v_sensor_id uuid;
BEGIN
    INSERT INTO air_quality.locations (name, latitude, longitude, neighborhood)
    VALUES (
      p_name, 
      p_long, p_lat, 'UNKNOWN'
    )
    ON CONFLICT (name, latitude, longitude)
    DO UPDATE SET name = p_name     -- This is a noop being used to ensure that the RETURNING clause always fires
    RETURNING location_id INTO v_location_id;
  
    INSERT INTO air_quality.sensors (location_id, name, status, extrnl_id, extrnl_source)
    VALUES (
      v_location_id,
      p_name,
      'Active',
      p_extrnl_id,
      p_extrnl_source
    )
    ON CONFLICT (extrnl_id, extrnl_source)
    DO UPDATE SET name = p_name     -- This is a noop being used to ensure that the RETURNING clause always fires
    RETURNING sensor_id INTO v_sensor_id;

    INSERT INTO air_quality.sensor_readings (sensor_id, recorded_at, pm1_0, pm2_5, pm10, temperature, humidity, pressure, quality_flag)
    VALUES (
      v_sensor_id,
      NOW(),
      p_pm1_0, p_pm2_5, p_pm10,
      p_temperature, p_humidity, p_pressure,
      'IGNORE'
    );
END;
$$;
