-- Aqi calculations for pm2.5 and pm10
-- Method: 24 hour trailing average concentration, converted to aqi



-- Equation 1: linear interpolation between two breakpoints
CREATE OR REPLACE FUNCTION air_quality.aqi_interpolate(
    concentration NUMERIC,
    bp_lo         NUMERIC,
    bp_hi         NUMERIC,
    aqi_lo        INTEGER,
    aqi_hi        INTEGER
) RETURNS INTEGER
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT ROUND(
        ((aqi_hi - aqi_lo)::NUMERIC / (bp_hi - bp_lo))
        * (concentration - bp_lo)
        + aqi_lo
    )::INTEGER;
$$;


-- Truncated to 1 decimal place 
CREATE OR REPLACE FUNCTION air_quality.pm25_aqi(concentration NUMERIC)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    c NUMERIC := TRUNC(concentration, 1);
BEGIN
    IF c IS NULL OR c < 0 THEN
        RETURN NULL;
    ELSIF c <= 9.0 THEN
        RETURN air_quality.aqi_interpolate(c, 0.0, 9.0, 0, 50);
    ELSIF c <= 35.4 THEN
        RETURN air_quality.aqi_interpolate(c, 9.1, 35.4, 51, 100);
    ELSIF c <= 55.4 THEN
        RETURN air_quality.aqi_interpolate(c, 35.5, 55.4, 101, 150);
    ELSIF c <= 125.4 THEN
        RETURN air_quality.aqi_interpolate(c, 55.5, 125.4, 151, 200);
    ELSIF c <= 225.4 THEN
        RETURN air_quality.aqi_interpolate(c, 125.5, 225.4, 201, 300);
    ELSE
        RETURN air_quality.aqi_interpolate(c, 225.5, 325.4, 301, 500);
    END IF;
END;
$$;


-- pm10 (ug/m3) -> aqi
-- Truncated to integer 
CREATE OR REPLACE FUNCTION air_quality.pm10_aqi(concentration NUMERIC)
RETURNS INTEGER
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
    c NUMERIC := TRUNC(concentration, 0);
BEGIN
    IF c IS NULL OR c < 0 THEN
        RETURN NULL;
    ELSIF c <= 54 THEN
        RETURN air_quality.aqi_interpolate(c, 0, 54, 0, 50);
    ELSIF c <= 154 THEN
        RETURN air_quality.aqi_interpolate(c, 55, 154, 51, 100);
    ELSIF c <= 254 THEN
        RETURN air_quality.aqi_interpolate(c, 155, 254, 101, 150);
    ELSIF c <= 354 THEN
        RETURN air_quality.aqi_interpolate(c, 255, 354, 151, 200);
    ELSIF c <= 424 THEN
        RETURN air_quality.aqi_interpolate(c, 355, 424, 201, 300);
    ELSE
        RETURN air_quality.aqi_interpolate(c, 425, 604, 301, 500);
    END IF;
END;
$$;

-- aqi value -> category descriptor
CREATE OR REPLACE FUNCTION air_quality.aqi_category(aqi INTEGER)
RETURNS VARCHAR
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT CASE
        WHEN aqi IS NULL THEN NULL
        WHEN aqi <= 50  THEN 'Good'
        WHEN aqi <= 100 THEN 'Moderate'
        WHEN aqi <= 150 THEN 'Unhealthy for sensitive groups'
        WHEN aqi <= 200 THEN 'Unhealthy'
        WHEN aqi <= 300 THEN 'Very unhealthy'
        ELSE 'Hazardous'
    END;
$$;


-- Current aqi per sensor: 24hour average of each pollutant,
-- converted to aqi, with the overall aqi and main pollutant
CREATE OR REPLACE VIEW air_quality.current_sensor_aqi AS
WITH pm_avgs AS (
    SELECT
        s.sensor_id,
        s.name AS sensor_name,
        s.location_id,
        AVG(r.pm2_5) FILTER (WHERE r.recorded_at > now() - INTERVAL '24 hours') AS pm2_5_24hr_avg,
        AVG(r.pm10)  FILTER (WHERE r.recorded_at > now() - INTERVAL '24 hours') AS pm10_24hr_avg
    FROM air_quality.sensors s
    LEFT JOIN air_quality.sensor_readings r
        ON r.sensor_id = s.sensor_id
       AND r.recorded_at > now() - INTERVAL '24 hours'
    GROUP BY s.sensor_id, s.name, s.location_id
        l.latitude,
        l.longitude,
        AVG(r.pm2_5) FILTER (
            WHERE r.recorded_at > now() - INTERVAL '24 hours'
        ) AS pm2_5_24hr_avg,
        AVG(r.pm10) FILTER (
            WHERE r.recorded_at > now() - INTERVAL '24 hours'
        ) AS pm10_24hr_avg
    FROM air_quality.sensors s
    JOIN air_quality.locations l
        ON l.location_id = s.location_id
    LEFT JOIN air_quality.sensor_readings r
        ON r.sensor_id = s.sensor_id
       AND r.recorded_at > now() - INTERVAL '24 hours'
    GROUP BY
        s.sensor_id,
        s.name,
        l.latitude,
        l.longitude
),
aqi_calc AS (
    SELECT
        sensor_id,
        sensor_name,
        location_id,
        latitude,
        longitude,
        pm2_5_24hr_avg,
        air_quality.pm25_aqi(pm2_5_24hr_avg) AS pm2_5_aqi,
        pm10_24hr_avg,
        air_quality.pm10_aqi(pm10_24hr_avg) AS pm10_aqi
    FROM pm_avgs
)
SELECT
    sensor_id,
    sensor_name,
    location_id,
    latitude,
    longitude,
    pm2_5_24hr_avg,
    pm2_5_aqi,
    pm10_24hr_avg,
    pm10_aqi,
    GREATEST(pm2_5_aqi, pm10_aqi) AS aqi,
    CASE
        WHEN pm2_5_aqi IS NULL AND pm10_aqi IS NULL THEN NULL
        WHEN COALESCE(pm2_5_aqi, -1) >= COALESCE(pm10_aqi, -1) THEN 'PM2.5'
        ELSE 'PM10'
    END AS main_pollutant,
    air_quality.aqi_category(GREATEST(pm2_5_aqi, pm10_aqi)) AS aqi_category
    air_quality.aqi_category(
        GREATEST(pm2_5_aqi, pm10_aqi)
    ) AS aqi_category
FROM aqi_calc;

-- Composite index to support the 24 hour window lookups
CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_recorded
    ON air_quality.sensor_readings (sensor_id, recorded_at);
