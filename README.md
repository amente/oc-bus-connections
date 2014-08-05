oc-bus-connections
==================

A work to find the average connection wait time for OC Transpo bus schedule. And possibly find an optimization to reduce it.This is a research conduted just out of curiousity and for learning.

The OC Transpo schedule data can be downloaded from
http://data.ottawa.ca/en/dataset/oc-transpo-schedules

The connection time is the time difference between the arrival time of one route at a given stop and the departure time (moslty similar to the arrival time) of another route from possible nearby stops. 

For the analysis,stops with in 50m distance are treated as nearby stops. To find the nearby stops for any given stop, a fixed radius near neighbours algorithm with 2D bucketing approach is used. This has a much better performance than a naive O(n^2) approach. Initial implementation of the naive approach on the given dataset (~5500 stops) took about 17 minutes to complete on a quad core 2.8GHz PC, where us the 2D bucketing approach took only few seconds. 

The 2D bucketing approach was hinted here: http://www.slac.stanford.edu/cgi-wrap/getdoc/slac-r-186.pdf.
In order to implement it, first all the stop coordinates had to be mapped to an XY grid (Different from the latiitude and longitude). The mapping approach involved defining a plane with three arbitrary stops and then defining axes and translating the coordinates of all stops on to the new plane.

The current analysis with all stops and routes considered, and also for scheduled trips with stops between 00:00 -- 23:59, resulted in an average connection time of 24 minutes.

A plan for future work is to re run the analysis for different time ranges, so that only important times are considered. Also, possible optimizations will be attempted.

Disclaimer: Not affliated with OC Transpo

