import os
import network_gen as gen
import tripdata_gen as tp
import sys  # Reading arguments
import json
from pprint import pprint
import config


def main(calculate_dist=False):
    print("############################### TRIP DATA SANDBOX ###############################")
    print("Creating trip data for '{}'.(from {} to {}).".format(
        config.tripdata["region"],
        config.tripdata["start"],
        config.tripdata["stop"]))
    

    # Create all folders where data will be saved
    if not os.path.exists(config.root_path):
        os.makedirs(config.root_path)

    if not os.path.exists(config.root_dist):
        os.makedirs(config.root_dist)

    if not os.path.exists(config.root_tripdata):
        os.makedirs(config.root_tripdata)
    
    if not os.path.exists(config.root_reachability):
        os.makedirs(config.root_reachability)

    print(("\n>>>>> Target folders:\n" +
          "\n - Distance matrix (csv) and dictionary (npy): {}" +
          "\n -   Data excerpt from NYC taxi dataset (csv): {}" +
          "\n -  Reachability (npy) & region centers (npy): {}.\n").format(
        config.root_dist,
        config.root_tripdata,
        config.root_reachability))

    # Get network graph and save
    G = gen.get_network_from(config.tripdata["region"],
                             config.root_path,
                             config.graph_name,
                             config.graph_file_name)
    gen.save_graph_pic(G)

    print( "\nGetting distance data...\n")
    # Creating distance dictionary [o][d] -> distance
    distance_dic = gen.get_distance_dic(config.path_dist_dic, G)

    # Creating distance matrix (n X n) from dictionary
    distance_matrix = gen.get_distance_matrix(G, distance_dic)
    
    # Distance matrix as dataframe
    dt_distance_matrix = gen.get_dt_distance_matrix(
        config.path_dist_matrix,
        distance_matrix)

    print(dt_distance_matrix.describe())

    # Creating reachability dictionary
    reachability = gen.get_reachability_dic(config.path_reachability_dic,
                                            distance_dic,
                                            step=config.step,
                                            total_range=config.total_range,
                                            speed_km_h=config.speed_km_h)

    # Creating region centers for all max. travel durations
    # in reachability dictionary
    region_centers = gen.get_region_centers(config.path_region_centers,
                                            reachability,
                                            root_path= config.root_reachability,
                                            step=config.step,
                                            total_range=config.total_range,
                                            speed_km_h=config.speed_km_h)

    ################# Processing trip data ###################################
    # Taxi data from NY city

    # Try downloading the raw data if not exists (NY)
    tp.download_file(config.tripdata["url_tripdata"],
                     config.root_tripdata,
                     config.tripdata_filename)

    # Get excerpt (start, stop)
    dt_tripdata = tp.get_trip_data(config.path_tripdata_source,
                                   config.path_tripdata,
                                   config.tripdata["start"],
                                   config.tripdata["stop"])

    # Adding street network node ids (from G) to tripdata
    tp.add_ids(config.path_tripdata, config.path_tripdata_ids, G, distance_dic)

if __name__ == "__main__":

    # execute only if run as a script
    main()
