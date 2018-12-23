import json
import config
import pandas as pd

import tripdata_gen as tp
import network_gen as nw

# REST - WSGI + Flask
from waitress import serve
from flask import Flask, jsonify

# Showing more columns
pd.set_option('display.max_columns', 100)

# Network
G = nw.load_network(config.graph_file_name, folder=config.root_path)

print("\n############## DATA DESCRIPTION #######################################")

print("\mReading tripdata from '{}'".format(config.path_tripdata_ids))
df = pd.read_csv(config.path_tripdata_ids,
                 parse_dates=True,
                 index_col="pickup_datetime")

print(df.describe())
print(df.info())
print(df.head(10))
print(df.tail(10))

app = Flask(__name__)

@app.route('/sp/<int:o>/<int:d>')
def sp(o, d):
    # http://127.0.0.1:5000/sp/1/900
    return ";".join(map(str, nw.get_sp(G, o, d)))


@app.route('/linestring_style/<int:o>/<int:d>/<stroke>/<float:width>/<float:opacity>')
def linestring_style(o, d, stroke, width, opacity):
    # Color comes with %23 to replace #
    # http://127.0.0.1:5000/linestring_style/1/900/%23FF0000/2.0/1.0
    return jsonify(nw.get_linestring(G, o, d, **{"stroke": stroke, "stroke-width": width, "stroke-opacity": opacity}))


@app.route('/point_style/<int:p>/<color>/<size>/<symbol>')
def point_style(p, color, size, symbol):
    # E.g.: http://127.0.0.1:5000/point_style/1/%23FF0000/small/circle
    return jsonify(nw.get_point(G, p, **{"marker-color": color, "marker-size": size, "marker-symbol": symbol}))


@app.route('/location/<int:id>')
def location(id):
    # http://127.0.0.1:5000/location/1
    return jsonify({"location": [G.node[id]["x"], G.node[id]["y"]]})


if __name__ == '__main__':

    serve(app, listen='*:5000')
    # print(linestring_style(0, 1, "#FF0000", 1.2,  1))
    # app.run(port='5000')