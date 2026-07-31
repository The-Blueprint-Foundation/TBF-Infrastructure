import datetime, random, csv, copy
from typing import override
from dateutil import relativedelta
from random_word import RandomWords
from texttable import Texttable
""" Simple Python script for generating an aqi backlog given a baseline """
placeholder: bool = True

Portland_Coordinate_Range = [
    (45.550_000, -122.550_000), #NW OF EAST
    (45.470_000, -122.505_000)  #SE OF EAST
]
Gresham_Coordinate_Range = [
    (45.530_000, -122.487_000), #NW OF GRESHAM
    (45.480_000, -122.390_000)  #SE OF GRESHAM
]

   # for day,lists_of_lists in enumerate(list_of_lists_of_lists):
   #     print(f"DAY: {day}")
   #     for fourth,lists in enumerate(lists_of_lists):
   #         print(f"\tCapture {fourth + 1} : {lists}")

class fake_sensor():
    sensor_name: str
    sensor_city: str
    sensor_latt: float
    sensor_long: float
    table: Texttable
    
    #sensor_location_name: tuple[str,str,float,float]
    data: list[list[list[float]]]
    data_dict : list[dict[str,str | float]]
    data_row = []
    
    date_start: datetime.datetime
    date_end  : datetime.datetime
    dates_length: int
    date_table_str = '%d-%m-%y %I%p'
    date_str = '%x'
    time_str = '%X%:z'
    id_date_str = '%d-%m-%y (%j)'
    def __init__(self, loc, data, start, end, length) -> None:
        random.seed()
        placeholder = datetime.time(hour=0,minute=0)
        self.sensor_name = loc[0]
        self.sensor_city = loc[1]
        self.sensor_latt = loc[2]
        self.sensor_long = loc[3]
        self.data = data.copy()
        self.data_dict = []


        self.date_start = datetime.datetime.combine(start,placeholder)
        self.date_end = datetime.datetime.combine(end,placeholder)
        self.dates_length = length
        self.table = Texttable().header(["DATE", "PM1", "PM2.5", "PM10", "TEMPERATURE (F)", "HUMIDITY"])
        self._set_data_rows()

    def _set_data_rows(self)->None:
        self.data_row = [[None] * 24 * 6] * self.dates_length
        current_date = self.date_start
        #EXAMPLE: 
        # | 01-01-2000 11AM | 1.2 | 1.3 | 1.4 | 1.7 | 1.8 |
        for days, lists_of_lists in enumerate(self.data):
            for hours,lists in enumerate(lists_of_lists):
                date    = current_date
                pm1     = lists[0]
                pm2_5   = lists[1]
                pm10    = lists[2]
                temp    = lists[3]
                humid   = lists[4]
                _ = self.table.add_row((date.strftime(self.date_table_str), pm1, pm2_5, pm10, temp, humid))
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
        return self.data_dict.__str__()

    def get_table(self)->str | None:
        return self.table.draw()

    def get_day(self, day: int)->list[list[float]]:
        data : list[list[float]] = []
        try:
            data = self.data[day]
        except IndexError as error:
            error.add_note(f"Could not retreive day {(self.date_start + datetime.timedelta(days=day)).strftime(self.id_date_str)} from sensor {self.sensor_name}, ")
            raise(error)
        return data

    @override
    def __str__(self):
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

sensors: list[fake_sensor]

#Update by 6 hours a day, (4 times a day) then average across all 6 hours,
# 0.5  / 4 = 0.125 (PM)
# 1.0  / 4 = 0.25 (HUMIDITY)
# (x/3)/ 4 = x/12 (TEMP)

#Update by 1 hour, (24 times a day)
# 0.5 / 24 = 0.02083_ ~~ 0.0208 (PM)
# 1.0 / 24 = 0.0416_  ~~ 0.0417 (HUMIDITY)
# (x/3)/24 = x/72               (TEMP)

def get_real_sensor_data(sensor_name: str)->list[list[float]]:
    """get_sensor_data placeholder to grab the data

    :param str sensor_name: name of sensor to grab from
    """
    #do some magic...
    data: list[list[float]]
    #data: dict[str,float] = {}
    data = [] #UPDATE
    if placeholder:
        #data = {
            #"pm1" : 20.0,
            #"pm2.5": 20.0,
            #"pm10": 5.0,
            #"temperature": 50.0,
            #"humidity": 70.0
        #}
        baseline = [20.0, 20.0, 5.0, 50.0, 70.0]
        for num in range(24):
            flt: float = num / 10
            data.append([x + flt for x in baseline])
    return data

def determine_weight(prev_weight: float, min_value: float, previous_value: float, max_value: float,  min_delta: float, previous_delta: float, max_delta: float):
    above_or_below = lambda max_val, prev_val, target : (max_val / prev_val) > target
    weight : float = 0.0
    percentile : float = 0.0
    rise_mult: float = 1.0
    fall_mult: float = 1.0
    percentiles = []
    for fi in range(11):
        curr: float = fi / 10
        percentiles.append([above_or_below(max_value,previous_value,curr),above_or_below(max_delta,previous_delta,curr)])
    for val_percent,del_percent in percentiles:
        if percentile == 0: continue
        if percentile < 0.25:
            rise_mult = 4
            fall_mult = 0.25
        if percentile < 0.5:
            rise_mult = 2
            fall_mult = 0.5
        if percentile == 0.5: #TRICK!
            rise_mult = 1.5
            fall_mult = 1.0
        if percentile > 0.5:
            rise_mult = 1
            fall_mult = 2
        if percentile > 0.75:
            rise_mult = 0.5
            fall_mult = 4
        
        #if val_percent and del_percent       : #HIGHER THAN PERCENTILE (HIGH), AND HIGHER DERIV (RISING)
            ##weight = prev_weight + (percentile / mult)
        #elif val_percent and not del_percent : #HIGHER THAN PERCENTILE (HIGH), AND LOWER  DERIV (FALLING)
            ##weight = prev_weight - percentile * mult
        #elif not val_percent and del_percent : #LOWER THAN PERCENTILE  (LOW) , AND HIGHER DERIV (RISING)
            ##weight = prev_weight + percentile * mult
        #else                                 : #LOWER THAN PERCENTILE  (LOW) , AND LOWER  DERIV (FALLING)
            ##weight = prev_weight - (percentile / mult)
        #percentile += 0.1

def get_fake_sensor_loc(name: str)->tuple[str,str,float,float]:
    place                               = ""
    ranges: list[tuple[float,float]]    = []
    long                                = 0.0
    latt                                = 0.0
    #is_g                                = False
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
    #Based on https://world-weather.info/forecast/usa/portland_2/2025/
    MAX_HUMIDITY = 84.0
    MIN_HUMIDITY = 58.0 
    return min(max(previous_value + random.uniform(-0.25, 0.25), MIN_HUMIDITY), MAX_HUMIDITY)

def generate_data_days(name_loc, today, today_data, start, end, total_size, swap_point)->fake_sensor:
    current_day    = today
    current_values = today_data[23]
    day_index      = 0
    sensor_days = [[[None] * 5] * 24] * total_size
    # DAYS
    # -> TIMES
    #   -> VALUES
    get_values = lambda prev_values, month : [get_pm(prev_values[0], "pm1"),get_pm(prev_values[1],"pm2.5"),get_pm(prev_values[2], "pm10"), get_temp(prev_values[3], month - 1), get_humidity(prev_values[4])]
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
            sensor_days[swap_point] = [x[:] for x in today_data]  # pyright: ignore[reportArgumentType, reportCallIssue]
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

def generate_data(before: datetime.date, today: datetime.date, after: datetime.date, number_sensors: int):
    """generate_data generate data based on trends within historical nw data
        Will break if range exceeds current year boundary, since relies on day of the year for calculation
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

    
    #sensor_days : tuple[tuple[str,str,float,float],list[tuple[datetime.time,float,float,float,float]]] = [None] * 10000
    sensor_names = [[None] * 4] * number_sensors

    if placeholder:
        today_data = get_real_sensor_data("PLACEHOLDER")
    else:
        today_data = get_real_sensor_data("") #UPDATE
    #Deltas for : pm1 | pm2.5 | pm10 | temp | humidity

    #get_values = lambda prev_values, month : [get_pm(prev_values[0], "pm1"),get_pm(prev_values[1],"pm2.5"),get_pm(prev_values[2], "pm10"), get_temp(prev_values[3], month - 1), get_humidity(prev_values[4])]

    #[SENSOR DATA]
    for num in range(number_sensors):
        sensor_names[num] = get_fake_sensor_loc(word.get_random_word())  # pyright: ignore[reportCallIssue, reportArgumentType]
        sensors.append(generate_data_days(name_loc=sensor_names[num], today=today, today_data=today_data, start=before, end=after, total_size=total_size, swap_point=swapping_point))

    
    #[LIST OF DAYS], 
    # [CURRENT DAY]
    #   [TIME]
    #   VALUES
    #current_day    = today
    #current_values = today_data
    #day_index      = 0
    #for day in range(total_size):
        #today_list = []
        #if day < swapping_point:
            ##Thank you https://stackoverflow.com/a/3240486
            #current_day -= datetime.timedelta(days=1)
            #current_month = current_day.month
            #day_index = swapping_point - day - 1
        #elif day > swapping_point:
            #current_day += datetime.timedelta(days=1)
            #current_month = current_day.month
            #day_index = day
        #else: # day == swapping_point
            #current_day = today
            #current_values = today_data
            #sensor_days[day_index] = today_data  # pyright: ignore[reportArgumentType, reportCallIssue]
            #continue

        #for twenty_fourth in range(24):
            #current_values = (datetime.time(hour=twenty_fourth,minute=0),get_values(current_values, current_month))
            #today_list.insert(twenty_fourth, current_values)  
        ##Thank you https://stackoverflow.com/a/2541874
        #sensor_days[day_index] = []
        #sensor_days[day_index] = [x[:] for x in today_list]
        #for i,values in enumerate(today_list):
            #sensor_days[day_index][i] = values[:]
    #return sensor_days
        
    #for day in range(before_size):
        #current_day -= datetime.timedelta(days=1)
        #current_month = current_day.month
        #day_list = [None] * 4
        #for fourth in range(4):
            #current_values = get_values(current_values, current_month)
            #day_list.insert(fourth, current_values)  # pyright: ignore[reportArgumentType]
        #sensor_days[before_size - day] = day_list
        #day_index += 1
    #current_day = today
    #current_values = today_data
    #sensor_days[day_index] = today_data  # pyright: ignore[reportArgumentType, reportCallIssue]
    #day_index += 1
    #for day in range(after_size):
        #current_day += datetime.timedelta(days=1)
        #current_month = current_day.month
        #day_list = [None] * 4
        #for fourth in range(4):
            #current_values=get_values(current_values, current_month)
            #day_list.insert(fourth,current_values)

def create_csv(sensors: list[fake_sensor], filename: str):
    #Thank you https://www.geeksforgeeks.org/python/working-csv-files-python/
    titles = ["Sensor Name", "Region", "Latitude", "Longitude", "Date", "Time", "PM1", "PM2.5", "PM10", "Temperature", "Humidity"]
    with open(filename, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=titles)
        writer.writeheader()
        for sensor in sensors:
            writer.writerows(sensor.data_dict)
    return

#def create_dummy():
    ##from psycopg2.extensions import connection
    ##Heavily relies on knowledge gained from: 
    ##https://www.geeksforgeeks.org/python/python-postgresql-create-database/
    ## NOTE REQUIRES TO CREATE 
    #db: psycopg2.extensions.connection = psycopg2.connect(
        #database="dummy",
        #user="postgres",
        #password="password",
        #host="localhost"
    #)
    #db.autocommit = True
    #db_cursor = db.cursor()

    #drop_sensors = """DROP TABLE sensors; """
    #drop_sensor_data = """ DROP TABLE sensors_data """

    #create_data = """ CREATE TABLE sensors_data (
        #id SERIAL PRIMARY KEY,
        #datetime DATETIME,
        #pm 1 FLOAT,
        #pm 2.5 FLOAT,
        #pm 10 FLOAT,
        #temperature f FLOAT,
        #humidity FLOAT
    #);"""

    #create_sensors = """ CREATE TABLE sensors  (
    #name VARCHAR(32) PRIMARY KEY,
    #longitude FLOAT,
    #latitude FLOAT 
    #id SERIAL FOREIGN KEY
    #);"""



    #create_sensor = """ INSERT INTO sensors VALUES (1,'portland_sensor',45.5,-122.65);"""
    
    #try: 
        #db_cursor.execute(drop_sensors)
    #except psycopg2.errors.UndefinedTable:
        #print("table sensors does not exist")
    #try:
        #db_cursor.execute(drop_sensor_data)
    #except psycopg2.errors.UndefinedTable:
        #print("table sensors data does not exist")
    #db_cursor.execute(create_sensors)
    #db_cursor.execute(create_data)
    #db_cursor.execute(create_sensor)
    #print(db.info)
    #db.close()

def get_date_range(before_months: int | None, after_months: int | None)->tuple[datetime.date,datetime.date,datetime.date]:
    if before_months is None:
        before_months = 6
    if after_months is None:
        after_months = 6
    today: datetime.date = datetime.date.today()
    before: datetime.date = today - relativedelta.relativedelta(months=before_months)
    after: datetime.date = today + relativedelta.relativedelta(months=after_months)

    return (before,today,after)
    #return (before.timetuple().tm_yday,today.timetuple().tm_yday,after.timetuple().tm_yday)

def pretty_display(list_of_lists_of_lists: list[list[list[None]]]):
    for day,lists_of_lists in enumerate(list_of_lists_of_lists):
        print(f"DAY: {day}")
        for fourth,lists in enumerate(lists_of_lists):
            print(f"\tCapture {fourth + 1} : {lists}")

def main()->None:
    """main acts as menu for generating a backlog, very baseline stuff
    """
    before_months = after_months = 1
    sensors_count = 2
    global sensors
    dates = get_date_range(before_months, after_months)
    generate_data(before=dates[0], today=dates[1], after=dates[2], number_sensors=sensors_count)
    for sensor in sensors:
        print(sensor)
    create_csv(sensors, 'file.csv')

if __name__ == "__main__":
    main()