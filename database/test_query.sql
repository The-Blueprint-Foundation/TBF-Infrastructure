/*TIMESTAMP*/
SELECT NOW();
SHOW datestyle;
/*LIST ALL CONNECTIONS */

/*TRY TO COPY */
\copy air_quality.locations FROM './locations_file.csv' WITH DELIMITER ',' CSV HEADER
\copy air_quality.sensors FROM './sensors_file.csv' WITH DELIMITER ',' CSV HEADER
\copy air_quality.sensor_readings FROM './sensor_readings_file.csv' WITH DELIMITER ',' CSV HEADER
