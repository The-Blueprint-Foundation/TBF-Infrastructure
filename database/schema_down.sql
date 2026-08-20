-- Teardown script for the sensor monitoring schema
-- Mirrors schema_up.sql and aqi_calculatior.sql.
-- Drops views, then functions, then tables in reverse


-- Mirrors schema_up.sql and aqi_calculator.sql.
-- Drops procedures, views, then functions, then tables in reverse

-- Procedures
DROP PROCEDURE IF EXISTS air_quality.submit_readings;

-- Views
DROP VIEW IF EXISTS air_quality.current_sensor_aqi;

-- Functions
DROP FUNCTION IF EXISTS air_quality.aqi_category;
DROP FUNCTION IF EXISTS air_quality.pm10_aqi;
DROP FUNCTION IF EXISTS air_quality.pm25_aqi;
DROP FUNCTION IF EXISTS air_quality.aqi_interpolate;

-- Tables 
DROP TABLE IF EXISTS air_quality.sensor_readings;
DROP TABLE IF EXISTS air_quality.sensors;
DROP TABLE IF EXISTS air_quality.locations;

-- Schema
DROP SCHEMA IF EXISTS air_quality;
