import csv
import datetime
import math

from geopy.distance import vincenty

SERVICE_TYPE = 'JUL18-JUL18DA-Weekday-01'
MAX_DISTANCE  = 50

#Read files into data strcutures, 
#There are some wierd characters "\xef\xbb\xbf" at the begining of the files

trips = {}
# Read all trips of for a given service type
with open('./google_transit/trips.txt', 'rb') as tripsfile:
    READER = csv.DictReader(tripsfile)
    for row in READER:
        if(row['service_id']==SERVICE_TYPE):
            trips[row['trip_id']] =row

stop_times = {}
# Read all stop times and construct a data structure indexed by stop_id and route_id
with open('./google_transit/stop_times.txt', 'rb') as stoptimesfile:
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
            a_t = [int(j) for j in stop_time['arrival_time'].split(':')]
            d_t = [int(j) for j in stop_time['departure_time'].split(':')]
            # Some times are above 23:59 hours need to ignore them
            if(a_t[0]<24):
                stop_time['arrival_time'] = datetime.time(a_t[0],a_t[1],a_t[2])
                stop_time['departure_time'] = datetime.time(d_t[0],d_t[1],d_t[2])
                valid_times.append(stop_time)
        stop_times[stop][route]= valid_times

# Read all stops
stops={}
with open('./google_transit/stops.txt', 'rb') as stopsfile:
    READER = csv.DictReader(stopsfile)
    for row in READER:
        row['stop_lat'] = float(row['stop_lat'])
        row['stop_lon'] = float(row['stop_lon'])
        stops[row['\xef\xbb\xbfstop_id']] = row

# For each stop find other stops with in MAX_DISTANCE
# This is a 'fixed radius near neighbours problem'
# We can use a naive approach or 2D bucketing approach.
# http://www.cs.wustl.edu/~pless/546/lectures/Lecture2.pdf
# http://algo.kaust.edu.sa/Documents/cs372l01.pdf
# http://www.slac.stanford.edu/cgi-wrap/getdoc/slac-r-186.pdf
'''
# A naive approach O(n^2)
# This takes a while to finish
start = time.time()
for stop1 in stops:
    if not stop1 in nearest_stops:
        nearest_stops[stop1] = set()
    for stop2 in stops:
        p1 = (stops[stop1]['stop_lat'],stops[stop1]['stop_lon'])
        p2 = (stops[stop2]['stop_lat'],stops[stop2]['stop_lon'])
        d= vincenty(p1,p2).meters
        if(d<=MAX_DISTANCE):
            nearest_stops[stop1].add(stop2)
'''

#Finds the distance between two stops
def find_distance(stop1,stop2):
    p1 = (stop1['stop_lat'],stop1['stop_lon'])
    p2 = (stop2['stop_lat'],stop2['stop_lon'])
    return vincenty(p1,p2).meters

# Inorder to use 2D bucketing approach we need to flatten out all stops
# as points in XY plane
stops_plane = {}

# Take three arbitrary stops as reference points
# to define a plane
s1 = stops['AF910']
s2 = stops['AA240']
s3 = stops['WI550']

#Precalculate distances between references for later speed up
d12 = find_distance(s1,s2)
d13 = find_distance(s1,s3)
d23 = find_distance(s2,s3)

stops_plane['AF910'] = (0,d12) # YAxis
stops_plane['AA240'] = (0,0) #Origin
stops_plane['WI550'] = (d23,0) #XAxis

#Finds the x,y coordinates for a stop on the defined plane
#Uses basic herons triangle area formula and law of cosines
def find_x_y(s):
    d1 = find_distance(s,s1)
    d2 = find_distance(s,s2)
    d3 = find_distance(s,s3)
    
    ky = (d2+d3+d23)/2    
    y = 2*math.sqrt(abs(ky*(ky-d2)*(ky-d3)*(ky-d23)))/d23

    kx = (d2+d1+d12)/2
    x = 2*math.sqrt(abs(kx*(kx-d2)*(kx-d1)*(kx-d12)))/d12

    #Determine signs
    if((d1*d1) < (d2*d2+d12*d12)):
        y= -1*y
        if(y == -0.0):
            y = 0.0
    if((d3*d3) < (d2*d2+d23*d23)):
        x= -1*x
        if(x==-0.0):
            x = 0.0
    return (x,y)

#Calculate coordinates of all stops
for stop in stops:
    stops_plane[stop] = find_x_y(stops[stop])

#print stops_plane['AF910']
#print stops_plane['AF920']

#Now use 2D bucket approach to find near neighbour stops
buckets = {}
size = round(MAX_DISTANCE/math.sqrt(2))
print size
def get_bucket_key(s):
    xdelta = stops_plane[s['\xef\xbb\xbfstop_id']][0]%(size)
    ydelta = stops_plane[s['\xef\xbb\xbfstop_id']][1]%(size) 
    x1 = stops_plane[s['\xef\xbb\xbfstop_id']][0] - xdelta
    x2 = x1+size
    y1 = stops_plane[s['\xef\xbb\xbfstop_id']][1] - ydelta
    y2 = y1+size

    return ((x1,y1),(x2,y2))
#Put stops in theie respective buckets
for stop in stops:
    key = get_bucket_key(stops[stop])
    if not key in buckets:
        buckets[key] = []
    buckets[key].append(stop)

# Finds the adjacent buckets for a given bucket
def get_adjacent_buckets(bucket):    
    x1 = bucket[0][0]
    y1 = bucket[0][1]     
    adj_buckets = []
    for i in [-2,-1,0,1,2]:
        for j in [-1,0,1]:
            adj_buckets.append(((x1+size*i,y1+size*j),(x1+size*(i+1),y1+size*(j+1))))
    for i in [-1,0,1]:
        for j in [-2,2]:
            adj_buckets.append(((x1+size*i,y1+size*j),(x1+size*(i+1),y1+size*(j+1))))  
    return adj_buckets

# Index nearest stops with a stop
nearest_stops = {} 
for stop in stops:
    if not stop in nearest_stops:
        nearest_stops[stop] = set()
    for bucket in get_adjacent_buckets(get_bucket_key(stops[stop])):
        if bucket in buckets:
            nearest_stops[stop].update(buckets[bucket])

