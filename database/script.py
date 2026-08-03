import datetime, random, csv, sys, getopt 
from typing import override
from dateutil import relativedelta
from random_word import RandomWords  # pyright: ignore[reportMissingTypeStubs]
from texttable import Texttable  # pyright: ignore[reportMissingTypeStubs]
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
    """fake_sensor class to hold the information for a fake sensor

    Contains a sensor with name, city, latitude, longitude, start/ end dates, and a table of data information.
    Attributes:
        sensor_name (str)                       : Name of sensor, for identification purposes
        sensor_city (str)                       : City for quick identification of latitude/longitude
        sensor_latt (float)                     : Longitude location of sensor
        sensor_long (float)                     : Latitude location of sensor
        table       (Texttable)                 : Table of information, in easily print/convertible format!
        data        (list[list[list[float]]])   : Raw information containing readings for every hour
    """    
    sensor_name: str
    sensor_city: str
    sensor_latt: float
    sensor_long: float
    table: Texttable
    
    #sensor_location_name: tuple[str,str,float,float]
    data: list[list[list[float]]]
    data_dict : list[dict[str,str | float]]
    data_row:list[list] = []
    
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
        self.__set_data_rows()

    def __set_data_rows(self)->None:
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
            error.add_note(f"Could not retrieve day {(self.date_start + datetime.timedelta(days=day)).strftime(self.id_date_str)} from sensor {self.sensor_name}, ")
            raise(error)
        return data

    def get_name(self)->str:
        return self.sensor_name

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

    
    sensor_names = [[None] * 4] * number_sensors

    if placeholder:
        today_data = get_real_sensor_data("PLACEHOLDER")
    else:
        today_data = get_real_sensor_data("") #UPDATE


    for num in range(number_sensors):
        sensor_names[num] = get_fake_sensor_loc(word.get_random_word())  # pyright: ignore[reportCallIssue, reportArgumentType]
        sensors.append(generate_data_days(name_loc=sensor_names[num], today=today, today_data=today_data, start=before, end=after, total_size=total_size, swap_point=swapping_point))

def create_csv(sensors: list[fake_sensor], filename: str):
    #Thank you https://www.geeksforgeeks.org/python/working-csv-files-python/
    titles = ["Sensor Name", "Region", "Latitude", "Longitude", "Date", "Time", "PM1", "PM2.5", "PM10", "Temperature", "Humidity"]
    with open(filename, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=titles)
        writer.writeheader()
        for sensor in sensors:
            writer.writerows(sensor.data_dict)
    return

def get_date_range(before_months: int | None, after_months: int | None)->tuple[datetime.date,datetime.date,datetime.date]:
    if before_months is None:
        before_months = 6
    if after_months is None:
        after_months = 6
    today: datetime.date = datetime.date.today()
    before: datetime.date = today - relativedelta.relativedelta(months=before_months)
    after: datetime.date = today + relativedelta.relativedelta(months=after_months)

    return (before,today,after)

def pretty_display(list_of_lists_of_lists: list[list[list[None]]]):
    for day,lists_of_lists in enumerate(list_of_lists_of_lists):
        print(f"DAY: {day}")
        for fourth,lists in enumerate(lists_of_lists):
            print(f"\tCapture {fourth + 1} : {lists}")

def addDotCsv(filename: str)->str:
    if ".csv" not in filename:
        filename += ".csv"
    return filename

def help()->None:
    msg=\
"""
Generates a range of fake data from a specified number of sensors, over a specified time period
Usage:      python3     script.py   [options]   <args>
  args are (in this order):
    beforeMonths                    Number of months before current date to model
    afterMonths                     Number of months after current date to model
    sensorCount                     Number of sensors to model
  options are (options may appear in any order):
    -h, --help                      Displays this message and exits
    -p, --print                     Display the sensor output after generation
    -d, --debug                     Displays every option / argument deciphered
    -o, --output=  filename         Specify file to send csv data, defaults to file.csv
    -n, --no-file                   Specify that file
"""
    print(msg)


def main()->None:
    """main acts as menu for generating a backlog, very baseline stuff
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
    #optionBools = [False,False,False]
    optionDict = {
        "help" : False,
        "print": False,
        "debug": False,
        "output": False,
        "no-file": False
    }
    argsList = [3,3,3]
    argsDict = {
        "before" : 3,
        "after"  : 3,
        "sensors": 3
    }
    
    exit = False


    args = sys.argv[1:]
    option = "hpdno:"
    alt_options = ["help", "print", "output", "debug", "no-file"]
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

            if exit is True:
                sys.exit(0)
        if optionDict.get("debug"):
            for option,values in optionDict.items():
                print(f'Option {option} = {values}')
            print(f'Argument List (beforeMonths, afterMonths, sensors)\n\tList: [{cmd_arguments}]')

        if not optionDict.get("no-file") and optionDict.get("output"):
            print(f'Note that options --output && --no-file chosen, running without outputting...')

        arg_count = len(cmd_arguments)
        if arg_count != 3:
            if arg_count < 3:
                print(f'Note, only {arg_count} arguments given, defaults to 3 months before, after, and sensors with default output to file.csv')
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
        sys.exit(0)
    except TypeError as error:
        print("Invalid Argument Given")
        print(str(error))
        help()
        sys.exit(0)
        
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
    if optionDict.get("print"):
        for sensor in sensors:
            print(sensor)
    if not optionDict.get("no-file"):
        create_csv(sensors, filename) 

if __name__ == "__main__":
    main()