import csv
from datetime import time
from geopy.distance import vincenty

SERVICE_TYPE = 'JUL18-JUL18DA-Weekday-01'
MAX_DISTANCE  = 50

stops={}
trips = {}
stop_times = {}

# Read all trips of for a given service type
with open('./transit_data/trips.txt', 'rb') as tripsfile:
    READER = csv.DictReader(tripsfile)
    for row in READER:
        if(row['service_id']==SERVICE_TYPE):
            trips[row['trip_id']] =row

# Read all stop times and construct a data structure indexed by stop_id and route_id
with open('./transit_data/stop_times.txt', 'rb') as stoptimesfile:
    READER = csv.DictReader(stoptimesfile)
    for row in READER:
        if(row['\xef\xbb\xbftrip_id'] in trips):
            stop_id = row['stop_id']
            trip_id = row['\xef\xbb\xbftrip_id']
            route_id = trips[trip_id]['\xef\xbb\xbfroute_id']
            if not stop_id in stop_times:
                stop_times[stop_id] = {}

            if not route_id in stop_times[stop_id]:
                stop_times[stop_id][route_id] = []

            stop_times[stop_id][route_id].append(row)

# Sort stop times for each route at stop based on arrival time, and convert times to time object
for stop in stop_times:
    for route in stop_times[stop]:
        stop_times[stop][route] = sorted(stop_times[stop][route],key = lambda stop_time: stop_time['arrival_time'])
        valid_times = []
        for i,stop_time in enumerate(stop_times[stop][route]):
            a_t = [int(x) for x in stop_time['arrival_time'].split(':')]
            d_t = [int(x) for x in stop_time['departure_time'].split(':')]
            # Some times are above 23:59 hours need to ignore them
            if(a_t[0]<24):
                stop_time['arrival_time'] = time(a_t[0],a_t[1],a_t[2])
                stop_time['departure_time'] = time(d_t[0],d_t[1],d_t[2])
                valid_times.append(stop_time)
        stop_times[stop][route]= valid_times

# Read all stops
with open('./transit_data/stops.txt', 'rb') as stopsfile:
    READER = csv.DictReader(stopsfile)
    for row in READER:
        stops[row['stop_id']] = row

#For each stop find other stops with in MAX_DISTANCE












