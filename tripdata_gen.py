import pandas as pd
import requests
import os
from multiprocessing import Pool
import osmnx as ox
from functools import partial
import network_gen as nw
import config


def download_file(url, root_path, file_name):
    """Download online file and save it.

    Arguments:
        url {String} -- Url to download
        output_file {String} -- Target path
    """

    output_file = "{}/{}".format(root_path, file_name)

    print("Loading  '{}'".format(output_file))

    if not os.path.exists(output_file):
        print("Downloading {}".format(url))
        r = requests.get(url, allow_redirects=True)
        open(output_file, 'wb').write(r.content)


def get_trip_data(tripdata_path, output_path, start=None, stop=None):
    """
    Read raw tripdata csv and filter unnecessary info.
    
        1 - Check if output path exists
        2 - If output path does not exist
            2.1 - Select columns ("pickup_datetime",
                                "passenger_count",
                                "pickup_longitude",
                                "pickup_latitude",
                                "dropoff_longitude",
                                "dropoff_latitude")
            2.2 - If start and stop are not None, get excerpt
        3 - Save clean tripdata in a csv
        3 - Return dataframe
    
    Arguments:
        tripdata_path {string} -- Raw trip data csv path
        output_path {string} -- Cleaned trip data csv path
        start {string} -- Datetime where tripdata should start (e.g., 2011-02-01 12:23:00)
        stop {string} -- Datetime where tripdata should end (e.g., 2011-02-01 14:00:00)
    
    Returns:
        Dataframe -- Cleaned tripdata dataframe
    """


    print("files:", output_path, tripdata_path)

    # Trip data dataframe (Valentine's day)
    tripdata_dt_excerpt = None

    try:

        # Load tripdata
        tripdata_dt_excerpt = pd.read_csv(
            output_path, parse_dates=True, index_col="pickup_datetime")

        print("Loading file '{}'.".format(output_path))

    except:

        # Columns used
        filtered_columns = ["pickup_datetime",
                            "passenger_count",
                            "pickup_longitude",
                            "pickup_latitude",
                            "dropoff_longitude",
                            "dropoff_latitude"]

        # Reading file
        tripdata_dt = pd.read_csv(tripdata_path,
                                  parse_dates=True,
                                  index_col="pickup_datetime",
                                  usecols=filtered_columns,
                                  na_values='0')

        tripdata_dt_excerpt = None

        # Get excerpt
        if start and stop:
            tripdata_dt_excerpt = pd.DataFrame(
                tripdata_dt.loc[(tripdata_dt.index >= start) & (tripdata_dt.index <= stop)])
        else:
            tripdata_dt_excerpt = pd.DataFrame(tripdata_dt)

        # Remove None values
        tripdata_dt_excerpt.dropna(inplace=True)

        # Sort
        tripdata_dt_excerpt.sort_index(inplace=True)

        # Save day data
        tripdata_dt_excerpt.to_csv(output_path)

    return tripdata_dt_excerpt


def get_ids(G,
            pk_lat,
            pk_lon,
            dp_lat,
            dp_lon,
            distance_dic_m,
            max_dist=50):

    try:
        # Get pick-up and drop-off coordinates of request
        pk = (pk_lat, pk_lon)
        dp = (dp_lat, dp_lon)

        # Get nearest node in graph from coordinates
        n_pk = ox.get_nearest_node(G, pk, return_dist=True)  # (id, dist)
        n_dp = ox.get_nearest_node(G, dp, return_dist=True)  # (id, dist)

        #print("Nearest:",n_pk, n_dp)

        # If nearest node is "max_dist" meters far from point, request is discarded
        if n_pk[1] > max_dist or n_dp[1] > max_dist:
            return [None, None]

        # pk must be different of dp
        if n_pk[0] == n_dp[0]:
            return [None, None]

        d = distance_dic_m[n_pk[0]][n_dp[0]]
        #print("Dist:", d)

        # Remove short distances
        if d >= max_dist:
            return [n_pk[0], n_dp[0]]
        else:
            return [None, None]
    except:
        return [None, None]


def add_ids_chunk(G, distance_dic_m, info):

    info[["pk_id", "dp_id"]] = info.apply(lambda row: pd.Series(get_ids(G,
                                                                        row['pickup_latitude'],
                                                                        row['pickup_longitude'],
                                                                        row['dropoff_latitude'],
                                                                        row['dropoff_longitude'],
                                                                        distance_dic_m)), axis=1)

    n = len(info)
    # Remove trip data outside Manhattan (street network in G)
    info.dropna(inplace=True)

    print("Adding ", len(info), "/", n)

    # Convert node ids and passenger count to int
    info[["passenger_count", "pk_id", "dp_id"]] = info[[
        "passenger_count", "pk_id", "dp_id"]].astype(int)

    # Reorder columns
    order = ['pickup_datetime',
             'passenger_count',
             'pk_id', 'dp_id',
             'pickup_latitude',
             'pickup_longitude',
             'dropoff_latitude',
             'dropoff_longitude']

    info = info[order]

    return info


def add_ids(path_tripdata,
            path_tripdata_ids,
            G,
            distance_dic_m):
    """[summary]
    
    Arguments:
        path_tripdata {[type]} -- [description]
        path_tripdata_ids {[type]} -- [description]
        G {[type]} -- [description]
        distance_dic_m {[type]} -- [description]
    """


    dt = None

    # if file does not exist write header
    if os.path.isfile(path_tripdata_ids):
    
        # Load tripdata
        dt = pd.read_csv(path_tripdata_ids,
                            parse_dates=True,
                            index_col="pickup_datetime")

        print("\nLoading trip data with ids...'{}'.".format(path_tripdata_ids))

    else:

        print("############ NY trip data ", path_tripdata, path_tripdata_ids)
        tripdata = pd.read_csv(path_tripdata)

        tripdata.info()

        # Number of lines to read from huge .csv
        chunksize = 2000

        # Redefine function to add graph and distances
        func = partial(add_ids_chunk, G, distance_dic_m)

        # Total number of lines
        togo = int(len(tripdata)/chunksize)

        # Read chunks of 500 lines
        # NY data filtered
        count = 0
        count_lines = 0

        # Multiprocesses
        n_mp = 8
        p = Pool(n_mp)

        list_parallel = []

        gen_chunks = pd.read_csv(
            path_tripdata, index_col=False, chunksize=chunksize)

        next_batch = next(gen_chunks)
        list_parallel.append(next_batch)

        while next_batch is not None:

            try:
                next_batch = next(gen_chunks)
                list_parallel.append(next_batch)
            except:
                next_batch = None

            # if info < chunksize, end reached. Process whatever is in parallel list
            if len(list_parallel) == n_mp or next_batch is None:

                count = count + len(list_parallel)
                count_lines = count_lines + sum(map(len, list_parallel))

                chunks_with_ids = p.map(func, list_parallel)

                for info_ids in chunks_with_ids:

                    # if file does not exist write header
                    if not os.path.isfile(path_tripdata_ids):

                        info_ids.to_csv(path_tripdata_ids,
                                        index=False)

                    # else it exists so append without writing the header
                    else:
                        info_ids.to_csv(path_tripdata_ids,
                                        mode="a",
                                        header=False,
                                        index=False)

                list_parallel.clear()
                print(count, "/", togo, " (", count_lines, "/", len(tripdata), ")")

        # Load tripdata
        dt = pd.read_csv(path_tripdata_ids, parse_dates=True,
                         index_col="pickup_datetime")
        print("\nLoading trip data with ids (after processing)...'{}'.".format(
            path_tripdata_ids))

    print(dt.head())
    print(dt.describe())
