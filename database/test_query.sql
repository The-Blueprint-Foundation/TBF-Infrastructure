/*TIMESTAMP*/
SELECT NOW();
SHOW datestyle;
/*LIST ALL CONNECTIONS */
\dt

/*TRY TO COPY */
\copy locations FROM './locations_file.csv' WITH DELIMITER ',' CSV HEADER
\copy sensors FROM './sensors_file.csv' WITH DELIMITER ',' CSV HEADER
\copy sensor_readings FROM './sensor_readings_file.csv' WITH DELIMITER ',' CSV HEADER
