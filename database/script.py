import datetime, random, csv, sys, getopt 
from typing import override
from dateutil import relativedelta
from random_word import RandomWords  # pyright: ignore[reportMissingTypeStubs]
from texttable import Texttable  # pyright: ignore[reportMissingTypeStubs]
""" Simple Python script for generating an aqi backlog given a baseline """
placeholder: bool = True

#Coordinate range of portland and gresham areas
Portland_Coordinate_Range = [
    (45.550_000, -122.550_000), #NW OF EAST
    (45.470_000, -122.505_000)  #SE OF EAST
]
Gresham_Coordinate_Range = [
    (45.530_000, -122.487_000), #NW OF GRESHAM
    (45.480_000, -122.390_000)  #SE OF GRESHAM
]


class fake_sensor():
    """fake_sensor class to hold the information for a fake sensor

    Contains a sensor with name, city, latitude, longitude, start/ end dates, and a table of data information.
    Attributes:
        sensor_name             (str)                           : Name of sensor, for identification purposes
        reading_id_count        (int)                           : Integer count of each hourly row data
        sensor_id               (int)                           : Unique ID of sensor given hash of name
        location_id             (int)                           : Unique ID of sensor given hash of latitude/longitude
        sensor_city             (str)                           : City for quick identification of latitude/longitude
        sensor_latt             (float)                         : Longitude location of sensor
        sensor_long             (float)                         : Latitude location of sensor
        table                   (Texttable)                     : Table of information, in easily print/convertible format!
        data                    (list[list[list[float]]])       : Raw information containing readings for every hour
        data_dict               (list[dict[str,str | float]])   : List of raw data rows as a dictionary
        data_row                (list[list])                    : List of lists of row data
        locations_dict          (list[dict[str,str|float|bool]]): List of location data row as a dictionary
        sensor_readings_dict    (list[dict[str,str|float]])     : List of sensor readings (hour by hour) data rows as a dictionary
        sensors_dict            (list[dict[str,str|int]])       : List of sensor information data row as a dictionary
        date_start              (datetime)                      : Datetime class that contains the date of which sensor 'starts'
        date_end                (datetime)                      : Datetime class that contains the date of which sensor 'ends'
        dates_length            (int)                           : Integer count of day difference between start and end date
    Constants:
        date_table_str          : "%d-%m-%y %I%p"               : String expression for datetime representation in table
        date_str                : "%x"                          : String expression for datetime representation for date specifically
        time_str                : "%X%:z"                       : String expression for datetime representation for time specifically
        id_date_str             : "%d-%m-%y (%j)"               : String expression for datetime representation for date/time, for csv table
        timestampz_str          : "%y-%m-%d %X%z"               : String expression for datetime representation for timestampz data type in postgresql
    """    
    sensor_name: str
    reading_id_count: int
    sensor_id  : int
    location_id: int
    sensor_city: str
    sensor_latt: float
    sensor_long: float
    table: Texttable
    
    data: list[list[list[float]]]
    data_dict : list[dict[str,str | float]]
    data_row:list[list] = []
    locations_dict : list[dict[str,str | float | bool]]
    sensor_readings_dict : list[dict[str,str | float]]
    sensors_dict : list[dict[str, str | int]]
    
    date_start: datetime.datetime
    date_end  : datetime.datetime
    dates_length: int
    date_table_str = '%d-%m-%y %I%p'
    date_str = '%x'
    time_str = '%X%:z'
    id_date_str = '%d-%m-%y (%j)'
    timestampz_str = '%y-%m-%d %X%z'
    def __init__(self, loc : tuple[str,str,float,float], data : list[list[list[float]]], start : datetime.date, end: datetime.date, length: int) -> None:
        """__init__ Create sensor given generated data

        Creates a fake sensor given location, time, and reading data

        :param tuple[str,str,float,float] loc: tuple containing the name of the sensor, city where sensor is, latitude of sensor, and longitude of sensor
        :param list[list[list[float]]] data: list of lists of lists of floats containing all sensor data -> [days [hours [individual readings]]]
        :param datetime.datetime start: datetime class of start date of readings
        :param datetime.datetime end: datetime class of end date of readings
        :param int length: timespan of given dates, as an integer
        """
        random.seed()
        start_of_day = datetime.time(hour=0,minute=0)

        self.sensor_name = loc[0]
        self.reading_id_count = 0
        self.sensor_id   = hash(self.sensor_name)
        self.sensor_city = loc[1]
        self.sensor_latt = loc[2]
        self.sensor_long = loc[3]
        self.location_id = hash(self.sensor_latt + self.sensor_long)

        self.data = data.copy()

        self.data_dict = []
        self.locations_dict = []
        self.sensors_dict = []
        self.sensor_readings_dict = []

        self.locations_dict.append(self.gen_loc_dict())
        self.sensors_dict.append(self.gen_sensors_dict())
        
        self.date_start = datetime.datetime.combine(start,start_of_day)
        self.date_end = datetime.datetime.combine(end,start_of_day)
        self.dates_length = length
        self.table = Texttable().header(["DATE", "PM1", "PM2.5", "PM10", "TEMPERATURE (F)", "HUMIDITY"])
        self.__set_data_rows()

    def __set_data_rows(self)->None:
        """__set_data_rows sets data from attributes into a texttable index of information

        Uses list of all information to generate a table row by row, iterating the date hour by hour in line with data
        """
        self.data_row = [[None] * 24 * 6] * self.dates_length
        current_date = self.date_start
        #EXAMPLE: 
        # | 01-01-2000 11AM | 1.2 | 1.3 | 1.4 | 1.7 | 1.8 |
        for _days, lists_of_lists in enumerate(self.data):
            for _hours,lists in enumerate(lists_of_lists):
                date    = current_date
                pm1     = lists[0]
                pm2_5   = lists[1]
                pm10    = lists[2]
                temp    = lists[3]
                humid   = lists[4]
                _ = self.table.add_row((date.strftime(self.date_table_str), pm1, pm2_5, pm10, temp, humid))
                current_hour: list[dict[str,str | float]] = self.gen_sensor_readings(lists, current_date)
                self.sensor_readings_dict.extend(current_hour)
                self.data_dict.append( dict([
                                            (str('Sensor Name'), self.sensor_name),
                                            (str('Region'), self.sensor_city),
                                            (str('Latitude'), self.sensor_latt),
                                            (str('Longitude'), self.sensor_long),
                                            (str('Date'), current_date.strftime(self.date_str)),
                                            (str('Time'), current_date.strftime(self.time_str)),
                                            (str('PM1'), pm1),
                                            (str('PM2.5'), pm2_5),
                                            (str('PM10'), pm10),
                                            (str('Temperature'), temp),
                                            (str('Humidity'), humid)
                                            ]))
                current_date += datetime.timedelta(hours=1)

    def get_dict_str(self)->str:
        """ :return str: returns dictionary as string representation
        """
        return self.data_dict.__str__()

    def gen_loc_dict(self)->dict[str, str | float | bool]:
        """gen_loc_dict Generates a dictionary containing sensor location

        Generates a location dictionary from sensor location data in format of csv row

        :return dict[str, str | float | bool]: Returns row of sensor location data as a dictionary
        """        
        location_id = self.location_id
        name        = self.sensor_name
        latitude    = self.sensor_latt
        longitude       = self.sensor_long   
        neighborhood   = self.sensor_city
        indoor          = False
        return dict([
                    (str("location_id"), location_id),
                    (str("name"), name),
                    (str("latitude"), latitude),
                    (str("longitude"), longitude),
                    (str("neighborhood"), neighborhood),
                    (str("indoor"), indoor)
                    ])

    def gen_sensors_dict(self)->dict[str, str | int]:
        """gen_sensors_dict Generates a sensor dictionary of sensor information

        Generates a sensor dictionary of sensor information in format of csv row

        :return dict[str, str | int]: Returns row of sensor information csv as a dictionary
        """        
        sensor_id   = self.sensor_id
        location_id = self.location_id
        name        = self.sensor_name
        status      = "Active"
        return dict([
                    (str("sensor_id"), sensor_id),
                    (str("location_id"),location_id),
                    (str("name"),name),
                    (str("status"),status)
                    ])

    def gen_sensor_readings(self, hour: list[float], time: datetime.datetime)->list[dict[str,str | float]]:
        """gen_sensor_readings Generates sensor readings dictionary for a specific hour

        Given a specific hour of data, generate a list of csv rows to input into sensor_readings

        :param list[float] hour: List of data to input
        :param datetime.datetime time: Datetime object to get timestampz string
        :return list[dict[str,str | float]]: List of sensor_readings rows as a list of dictionary
        """
        #"reading_id", "sensor_id", "measurement_type", "unit", "value", "recorded_at", "quality_flag"
        readings: list[dict[str,str | float]] = []
        current_reading_id = self.reading_id_count
        sensor_id = self.sensor_id
        measurement_types = ["pm1", "pm2.5", "pm10", "Temperature", "Humidity"]
        units = ["Micrograms per cubic meter", "Micrograms per cubic meter","Micrograms per cubic meter","Fahrenheit", "Relative Humidity (Percentage)"]
        #value = hour[type]
        recorded_at = time.strftime(self.timestampz_str)
        quality_flag = "Good"
        for i in range(len(hour)):
            readings.append(   dict([
                                    (str("reading_id"), current_reading_id),
                                    (str("sensor_id"), sensor_id),
                                    (str("measurement_type"), measurement_types[i]),
                                    (str("unit"), units[i]),
                                    (str("value"), hour[i]),
                                    (str("recorded_at"), recorded_at),
                                    (str("quality_flag"), quality_flag)
                                    ]))
            current_reading_id += 1
        return readings

    def get_table(self)->str | None:
        """ :return str: returns generated texttable as string using draw() function"""
        return self.table.draw()

    def get_day(self, day: int)->list[list[float]]:
        """get_day gets day of sensor readings

        gets day of sensor readings (24 count hour readings)

        :param int day: day as index of day list
        :return list[list[float]]: returns list of hourly readings at specified date
        """
        data : list[list[float]] = []
        try:
            data = self.data[day]
        except IndexError as error:
            error.add_note(f"Could not retrieve day {(self.date_start + datetime.timedelta(days=day)).strftime(self.id_date_str)} from sensor {self.sensor_name}, ")
            raise(error)
        return data

    def get_name(self)->str:
        """ :return str: returns sensor name """
        return self.sensor_name

    @override
    def __str__(self)->str:
        """ Utilizes texttable module to print a small card containing location / id information of sensor, and table containing all data
            :return str: returns string representation of card + table
        """
        line=\
        f"""
            /------------------------\\
            | Sensor                 | {self.sensor_name}
            | City                   | {self.sensor_city}
            | Latitude, Longitude    | {self.sensor_latt}, {self.sensor_long}
            \\------------------------/\n"""
        table = self.get_table()
        table_str : str
        if table is None:
            table_str = "No entries listed"
        else:
            table_str = str(table)
            
        return line + table_str

#global list of sensors, used for efficiency sake
sensors: list[fake_sensor]

def get_real_sensor_data(sensor_name: str)->list[list[float]]:
    """get_sensor_data placeholder to grab the data

    :param str sensor_name: name of sensor to grab from
    """
    #do some magic...
    sensor_info: list[list[float]] = []
    def populate_fake_hour_floats(baseline: list[float])->None:
        for num in range(24):
            flt: float = num / 10
            sensor_info.append([x + flt for x in baseline])
    if placeholder:
        baseline = [20.0, 20.0, 5.0, 50.0, 70.0]
        populate_fake_hour_floats(baseline)
        
    else:
        #get_data
        raise NotImplementedError(f"Note getting the data from sensor is not implemented, therefore {sensor_name} cannot be accessed!")
    return sensor_info

def get_fake_sensor_loc(name: str)->tuple[str,str,float,float]:
    """get_fake_sensor_loc Generates fake location data and returns as tuple

    Takes name of sensor and generates fake latitude, longitude, and city in service of returning a tuple containing all sensor id information

    :param str name: Name of sensor to include in tuple
    :return tuple[str,str,float,float]: tuple consisting of name,city,latitude,longitude of fake sensor
    """
    place                               = ""
    ranges: list[tuple[float,float]]    = []
    long                                = 0.0
    latt                                = 0.0
    g = str("Gresham")
    p = str("East Portland")
    
    g_or_p = random.randint(0,1)
    if g_or_p:
        place = g
        ranges = Gresham_Coordinate_Range
    else:
        place = p
        ranges = Portland_Coordinate_Range
    LEFTEST  = ranges[0][0]
    RIGHTEST = ranges[1][0]
    TOP      = ranges[0][1]
    BOTTOM   = ranges[1][1]
    latt = random.uniform(LEFTEST, RIGHTEST)
    long = random.uniform(BOTTOM, TOP)
    return (name,place,latt,long)

def get_temp(previous_value: float, month: int)->float:
    """get_temp Generates temperature reading to be given back to sensor

    Generates temperature reading given previous value and month 'taken' to simulate believable variation in data
    
    :param float previous_value: Previous temperature generated, base case is placeholder / actually pulled data
    :param int month: Month as integer from 0-11
    :return float: Returns temperature (in Fahrenheit!)
    """
    MAX = 0
    MIN = 1

    #Based on https://www.extremeweatherwatch.com/cities/portland-or/year-2025
    #Temperature| Months | Max | Min |
    TEMPS_MAX_MIN= [(54.0, 25.0), #"January"  
                    (70.0, 24.0), #"February" 
                    (82.0, 36.0), #"March"    
                    (81.0, 37.0), #"April"    
                    (86.0, 40.0), #"May"      
                    (96.0, 47.0), #"June"     
                    (97.0, 54.0), #"July"     
                    (102.0,54.0), #"August"   
                    (90.0, 48.0), #"September"
                    (79.0, 39.0), #"October"  
                    (62.0, 34.0), #"November" 
                    (62.0, 31.0)  #"December" 
                    ]
    max_change = previous_value / 12
    delta      = max_change * random.uniform(-1.0, 1.0)
    new_temp   = delta + previous_value
    return min(max(new_temp,TEMPS_MAX_MIN[month][MIN]),TEMPS_MAX_MIN[month][MAX])

def get_pm(previous_value: float, pm_type: str | int)->float:
    """get_pm Generates fake sensor information for pm1, pm2.5 and pm10 readings

    Generates fake sensor data given previous pm value and the type of pm being faked to generate a believable variation in 
    data of pm readings
    
    :param float previous_value: Previous pm value generated, base case being placeholder / actually pulled pm value
    :param str | int pm_type: Type of pm (pm1,pm2.5, or pm10) as either string literal or int corresponding to list of pms
    :raises ValueError: Raises value error if given invalid string
    :raises TypeError: Raises type error if not string or int, since cannot gather pm info without specified type
    :return float: Returns newly generated pm value
    """
    #Based on https://www.epa.gov/air-trends/particulate-matter-pm25-trends for northwest
    MAX_PM1  = 38.0
    MAX_PM25 = 30.7
    MAX_PM10 = 10.0
    MAX_PMS_DICT  = {
        "pm1"  : MAX_PM1,
        "pm2.5": MAX_PM25,
        "pm25" : MAX_PM25,
        "pm10" : MAX_PM10,
    }
    MAX_PMS_INT = [MAX_PM1,MAX_PM25,MAX_PM10]
    MIN = 0
    max_pm : float
    if type(pm_type) is str:
        tmp = MAX_PMS_DICT.get(pm_type)
        if tmp is None:
            raise ValueError(f"Called get pm using improper pm value type:\nParameters: {previous_value}, {pm_type}")
        max_pm = tmp
    elif type(pm_type) is int:
        max_pm = MAX_PMS_INT[pm_type]
    else:
        raise TypeError(f"Called get pm without using proper type of pm_type:\nParameters: {previous_value}, {pm_type}")
        
    #pm_delta = 0.5 is max change I can see in data
    return min(max(previous_value + random.uniform(-0.125,0.125), MIN), max_pm)

def get_humidity(previous_value: float)->float:
    """get_humidity Generates fake humidity reading 

    Generates fake humidity reading given previous humidity values

    :param float previous_value: Previous humidity reading, base case being placeholder / actually pulled humidity
    :return float: Returns newly generated humidity reading
    """
    #Based on https://world-weather.info/forecast/usa/portland_2/2025/
    MAX_HUMIDITY = 84.0
    MIN_HUMIDITY = 58.0 
    return min(max(previous_value + random.uniform(-0.25, 0.25), MIN_HUMIDITY), MAX_HUMIDITY)

def generate_data_days(name_loc ,today: datetime.date, today_data: list[list[float]], start: datetime.date, end: datetime.date, total_size: int, swap_point: int)->fake_sensor:
    """generate_data_days collates all the given data to return a sensor with fake data

    Uses given sensor_id and date range to generate & return a new fake sensor class containing all relevant data

    :param tuple[str,str,float,float] name_loc: Tuple containing name,city,latitude, and longitude of sensor
    :param datetime.date today: Date of today, the middle point
    :param list[list[float]] today_data: list of hourly readings of today either placeholder or actually pulled
    :param datetime.date start: Start date of sensor readings
    :param datetime.date end: End date of sensor readings
    :param int total_size: Total number of days to generate
    :param int swap_point: Halfway point at which to swap from generating backward to generating forward
    :return fake_sensor: Returns fake sensor class that holds all relevant data
    """
    current_day    = today
    current_values = today_data[23]
    day_index      = 0
    sensor_days: list[list] = [[[None] * 5] * 24] * total_size
    # DAYS
    # -> TIMES
    #   -> VALUES
    def get_values(prev_values: list[float], month: int)->list[float]:
        pm1 = get_pm(prev_values[0], "pm1")
        pm2_5 = get_pm(prev_values[1], "pm25")
        pm10 = get_pm(prev_values[2], "pm10")
        temp = get_temp(prev_values[3], month)
        humidity = get_humidity(prev_values[4])
        return [pm1,pm2_5,pm10,temp,humidity]

    for day in range(total_size):
        today_list = []
        if day < swap_point:
            #Thank you https://stackoverflow.com/a/3240486
            current_day -= datetime.timedelta(days=1)
            current_month = current_day.month
            day_index = swap_point - day - 1
        elif day > swap_point:
            current_day += datetime.timedelta(days=1)
            current_month = current_day.month
            day_index = day
        else: # day == swapping_point
            current_day = today
            sensor_days[swap_point] = [x[:] for x in today_data]  
            continue

        for twenty_fourth in range(24):
            current_values = get_values(current_values, current_month)
            today_list.insert(twenty_fourth, current_values)
        #Thank you https://stackoverflow.com/a/2541874
        sensor_days[day_index] = []
        sensor_days[day_index] = [x[:] for x in today_list]
        for i,values in enumerate(today_list):
            sensor_days[day_index][i] = values[:]
    return fake_sensor(loc=name_loc, data=sensor_days, start=start,end=end,length=total_size)

def generate_data(before: datetime.date, today: datetime.date, after: datetime.date, number_sensors: int)->None:
    """generate_data Generates all sensors

    Generates full range of sensors given date range and number of fake sensors to create

    :param datetime.date before: Earliest date of sensor readings
    :param datetime.date today: Date of sensor readings from which rest propagate (either forwards or backwards)
    :param datetime.date after: Latest date of sensor readings
    :param int number_sensors: Number of sensors to generate given as an integer

    Appends to global sensor list rather than return list of classes
    """
    random.seed()
    word = RandomWords()
    today_data = []
    BEFORE = 0
    TODAY  = 1
    AFTER  = 2
    global sensors
    sensors = []

    days_of_year : list[int] = [before.timetuple().tm_yday, today.timetuple().tm_yday, after.timetuple().tm_yday]
    before_size = days_of_year[TODAY] - days_of_year[BEFORE] - 1
    total_size  = days_of_year[AFTER] - days_of_year[BEFORE]
    swapping_point = total_size - before_size

    
    sensor_names = [[None] * 4] * number_sensors

    if placeholder:
        today_data = get_real_sensor_data("PLACEHOLDER")
    else:
        today_data = get_real_sensor_data("") #UPDATE


    for num in range(number_sensors):
        sensor_names[num] = get_fake_sensor_loc(word.get_random_word())  # pyright: ignore[reportCallIssue, reportArgumentType]
        sensors.append(generate_data_days(name_loc=sensor_names[num], today=today, today_data=today_data, start=before, end=after, total_size=total_size, swap_point=swapping_point))

def create_locations_csv(sensors: list[fake_sensor], filename: str)->None:
    """create_locations_csv Creates csv of sensor locations

    Creates and outputs a new csv file of locations of each sensor with format locations_<filename>.csv from each sensor

    :param list[fake_sensor] sensors: List of sensors from which to draw from
    :param str filename: Name of file suffix to write csv data
    """    
    titles = ["location_id", "name", "latitude", "longitude", "neighborhood", "indoor"]
    with open("locations_" + filename, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=titles)
        writer.writeheader()
        for sensor in sensors:
            writer.writerows(sensor.locations_dict)
    return

def create_sensors_csv(sensors: list[fake_sensor], filename: str)->None:
    """create_sensors_csv Creates a csv of sensor information

    Creates and outputs a new csv file of sensor information with format sensors_<filename>.csv from each sensor

    :param list[fake_sensor] sensors: List of sensors from which to draw from
    :param str filename: Name of file suffix to write csv data
    """    
    titles = ["sensor_id", "location_id", "name", "status"]
    with open("sensors_" + filename, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=titles)
        writer.writeheader()
        for sensor in sensors:
            writer.writerows(sensor.sensors_dict)
    return

def create_sensor_readings_csv(sensors: list[fake_sensor], filename: str)->None:
    """create_sensor_readings_csv Creates csv of sensor readings (hourly readings)

    Creates and outputs a new csv file of sensor data with format sensor_readings_<filename>.csv from each sensor
    
    :param list[fake_sensor] sensors: List of fake sensors from which to write csv data
    :param str filename: Name of file suffix to write csv data
    """    
    titles = ["reading_id", "sensor_id", "measurement_type", "unit", "value", "recorded_at", "quality_flag"]
    with open("sensor_readings_" + filename, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=titles)
        writer.writeheader()
        for sensor in sensors:
            writer.writerows(sensor.sensor_readings_dict)
    return

def create_data_csv(sensors: list[fake_sensor], filename: str)->None:
    """create_csv Creates raw csv of sensor data

    Creates and outputs a new csv file of specified name from list of generated fake sensors of raw data

    :param list[fake_sensor] sensors: List of fake sensors from which to write csv data
    :param str filename: Name of file to write csv data
    """
    #Thank you https://www.geeksforgeeks.org/python/working-csv-files-python/
    titles = ["Sensor Name", "Region", "Latitude", "Longitude", "Date", "Time", "PM1", "PM2.5", "PM10", "Temperature", "Humidity"]
    with open("data_" + filename, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=titles)
        writer.writeheader()
        for sensor in sensors:
            writer.writerows(sensor.data_dict)
    return

def get_date_range(before_months: int | None, after_months: int | None)->tuple[datetime.date,datetime.date,datetime.date]:
    """get_date_range Gets date range from integer count of months

    Gets range of dates given number of previous / subsequent months as integer number

    :param int | None before_months: Number of months to generate back
    :param int | None after_months: Number of months to generate forward
    :return tuple[datetime.date,datetime.date,datetime.date]: tuple consisting of earliest,today, and latest dates
    """
    if before_months is None:
        before_months = 6
    if after_months is None:
        after_months = 6
    today: datetime.date = datetime.date.today()
    before: datetime.date = today - relativedelta.relativedelta(months=before_months)
    after: datetime.date = today + relativedelta.relativedelta(months=after_months)

    return (before,today,after)

def pretty_display(list_of_lists_of_lists: list[list[list[None]]]):
    """pretty_display Quick and painless view of all data

    Given raw data of sensor information, prints a quick readable list of information. For debugging purposes
    :param list[list[list[None]]] list_of_lists_of_lists: Raw data of sensor information
    """
    for day,lists_of_lists in enumerate(list_of_lists_of_lists):
        print(f"DAY: {day}")
        for fourth,lists in enumerate(lists_of_lists):
            print(f"\tCapture {fourth + 1} : {lists}")

def addDotCsv(filename: str)->str:
    """addDotCsv Adds .csv to filename if not added

    Adds .csv to filename if not present, returns newly verified filename

    :param str filename: Filename to verify
    :return str: Returns name of file plus .csv, ensuring an actual readable file
    """
    if ".csv" not in filename:
        filename += ".csv"
    return filename

def help()->None:
    """help Contains multi-line help string that prints
    """
    msg=\
    """
    Generates a range of fake data from a specified number of sensors, over a specified time period,
    Outputting to 3 separate csv files with default suffix of 'file' and of form : 
        locations_<suffix>.csv 
        sensors_<suffix>.csv
        sensor_readings<suffix>.csv

    Usage:      python3     script.py   [options]   <args>
    args are (in this order):
        beforeMonths                    Number of months before current date to model
        afterMonths                     Number of months after current date to model
        sensorCount                     Number of sensors to model
    options are (options may appear in any order):
        -h, --help                      Displays this message and exits
        -p, --print                     Display the sensor output after generation
        -d, --debug                     Displays every option / argument deciphered + additional data
        -o, --output=  filename         Specify file suffix for csv files (default is 'file')
        -n, --no-file                   Specify no csv file output
        -r, --raw                       Toggle data_<suffix>.csv that displays all information in one csv
    """
    print(msg)

def main()->None:
    """main acts as menu for generating a range of sensors & outputs to csv unless specified
    """
    global sensors
    filename = "file.csv"

    HELP_L = "--help"
    HELP_S = "-h"
    PRINT_L= "--print"
    PRINT_S= "-p"
    OUT_L  = "--output"
    OUT_S  = "-o"
    DEBUG_S= "-d"
    DEBUG_L= "--debug"
    NFILE_S= "-n"
    NFILE_L= "--no-file"
    RAW_S  = "-r"
    RAW_L  = "--raw"
    optionDict = {
        "help" : False,
        "print": False,
        "debug": False,
        "output": False,
        "no-file": False,
        "raw"    : False
    }
    argsList = [3,3,3]
    argsDict = {
        "before" : 3,
        "after"  : 3,
        "sensors": 3
    }
    
    exit = False


    args = sys.argv[1:]
    option = "hpdnro:"
    alt_options = ["help", "print", "output", "debug", "no-file", "raw"]
    try: 
        cmd_options,cmd_arguments = getopt.getopt(args,option,alt_options)
        for current_opt, current_value in cmd_options:
            if current_opt in (HELP_S, HELP_L):     #HELP
                optionDict.update({"help" : True})
                help()
                exit = True
            elif current_opt in (PRINT_S, PRINT_L): #PRINT
                optionDict.update({"print" : True})
            elif current_opt in (OUT_S, OUT_L):
                optionDict.update({"output" : True})
                filename=addDotCsv(current_value)   #
            elif current_opt in (DEBUG_S, DEBUG_L):
                optionDict.update({"debug" : True})
            elif current_opt in (NFILE_S, NFILE_L):
                optionDict.update({"no-file" : True})
            elif current_opt in (RAW_S, RAW_L):
                optionDict.update({"raw" : True})
            if exit is True:
                sys.exit(0)
        if optionDict.get("debug"):
            for option,values in optionDict.items():
                print(f'Option {option} = {values}')
            print(f'Argument List (beforeMonths, afterMonths, sensors)\n\tList: [{cmd_arguments}]')

        if optionDict.get("no-file") and optionDict.get("output"):
            print(f'Note that options --output && --no-file chosen, ignoring no file...')
        if optionDict.get("no-file") and optionDict.get("raw"):
            print('Note that options --raw && --no-file chosen, ignoring no file...')

        arg_count = len(cmd_arguments)
        if arg_count != 3:
            if arg_count < 3:
                print(f'Note, only {arg_count} arguments given, defaults to 3 months before, after, and sensors with default output to file.csv as suffix')
            if arg_count > 3:
                assert False, f"Too many args given, expect 3 but {arg_count} given..."

        for count,value in enumerate(cmd_arguments):
            argsList[count] = int(value)
        count = 0
        for entry in argsDict:
            argsDict.update({f"{entry}" : argsList[count]})
            count += 1
            
    except getopt.error as error:
        print(str(error))
        help()
        sys.exit(1)
    except TypeError as error:
        print("Invalid Argument Given")
        print(str(error))
        help()
        sys.exit(2)
    except AssertionError as error:
        print(str(error))
        help()
        sys.exit(3)
        
    before_months = argsList[0]
    after_months  = argsList[1]
    sensors_count = argsList[2]
    dates = get_date_range(before_months, after_months)
    generate_data(before=dates[0], today=dates[1], after=dates[2], number_sensors=sensors_count)
    if optionDict.get("debug"):
        sensor_count = len(sensors)
        print(f"PRINTING SENSORS, COUNT: {sensor_count}")
        for sensor in range(sensor_count):
            print(f'    Sensor {sensor} : {sensors[sensor].get_name()}')
            print('---First four days---')
            days: list[list[list]] = [sensors[sensor].get_day(0), sensors[sensor].get_day(1), sensors[sensor].get_day(2), sensors[sensor].get_day(3)]
            pretty_display(days)
    if optionDict.get("print"):
        for sensor in sensors:
            print(sensor)
    if not optionDict.get("no-file"):
        if optionDict.get("raw"):
            create_data_csv(sensors, filename) 
        create_locations_csv(sensors, filename)
        create_sensors_csv(sensors, filename)
        create_sensor_readings_csv(sensors,filename)

if __name__ == "__main__":
    main()