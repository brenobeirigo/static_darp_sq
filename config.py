import os
import json
from pprint import pprint


def get_excerpt_name(start, stop):
    return "tripdata_excerpt_{}_{}".format(start, stop).replace(":", "").replace(" ", "_")


root_path = os.getcwd().replace("\\", "/")+"/data"
root_tripdata = root_path + "/tripdata"
root_dist = root_path + "/dist"

###### Reachability
# Reachability layers (e.g., reachable in 30, 60, ..., total_range steps)
step = 30 
total_range=600
# If defined, step and total_range are assumed to be seconds
speed_km_h = 30
root_reachability = root_path + "/reachability_{}_{}{}".format(step, total_range, ("_kmh{}".format(speed_km_h) if speed_km_h else ""))

# Input data
tripdata = None
with open("config/config_tripdata.json") as js:
    tripdata = json.load(js)
    #print("Trip data:")
    #pprint(tripdata)

# Config
db_connection = None
with open('config/db_config.json') as js:
    db_connection = json.load(js)
    #print("\nDB connection data:")
    #pprint(db_connection)

# Path of trip data with ids
path_tripdata_ids = "{}/{}_ids.csv".format(root_tripdata,
                                           get_excerpt_name(
                                               tripdata["start"],
                                               tripdata["stop"]))

# Create and store graph name
graph_name = tripdata["region"].lower().replace(" ", "-").replace(",", "")

# Distance matrix
path_dist_matrix = "{}/distance_matrix_m_{}.csv".format(root_dist, graph_name)

# Distance dictionary (meters)
path_dist_dic = "{}/distance_dic_m_{}.npy".format(root_dist, graph_name)

# Reachability dictionary {o =  {max_dist =[d1, d2, d3]}
path_reachability_dic = "{}/reachability_{}.npy".format(root_reachability, graph_name)

# Region centers dictionary {max_dist = [c1, c2, c3, c4, c5]}
path_region_centers = "{}/region_centers_{}.npy".format(root_reachability, graph_name)

# Presumably, the last part of the url is the file name
tripdata_filename = tripdata["url_tripdata"].split("/")[-1]
path_tripdata_source = "{}/{}".format(root_tripdata, tripdata_filename)

path_tripdata = "{}/{}.csv".format(root_tripdata,
                                   get_excerpt_name(
                                   tripdata["start"],
                                   tripdata["stop"]))

# Create and store graph name
graph_name = tripdata["region"].lower().replace(" ", "-").replace(",", "")
graph_file_name = "{}.graphml".format(graph_name)


