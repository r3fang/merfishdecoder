import geopandas as geo
from merfishdecoder.core import dataset
import os
import numpy as np
from shapely.strtree import STRtree
import sys

def main():
    dataSetName = sys.argv[1]
    dataSet = dataset.MERFISHDataSet(
            dataSetName)

    # change working directory
    os.chdir(dataSet.analysisPath)
    clusterFileName = "exportedFeatures/clusters.shp"
    nucleusFileName = "exportedFeatures/DAPI.shp"
    polyTFileName = "exportedFeatures/polyT.shp"

    # read features
    cluster = geo.read_file(
        clusterFileName)
    nucleus = geo.read_file(
        nucleusFileName)
    poly = geo.read_file(
        polyTFileName)

    nucleus["idx"] = np.arange(nucleus.shape[0])
    cluster["idx"] = np.arange(cluster.shape[0])
    poly["idx"] = np.arange(poly.shape[0])

    # find clusters that overlap with cell
    tree = STRtree(nucleus.geometry)
    overlaps = np.array([ len(tree.query(x)) > 0 \
        for x in cluster.geometry ])
    cluster = cluster[~overlaps]

    tree = STRtree(poly.geometry)
    overlaps = np.array([ len(tree.query(x)) > 0 \
        for x in cluster.geometry ])
    cluster = cluster[~overlaps]

    cluster.to_file(
        "exportedFeatures/dendrite.shp")

if __name__ == "__main__":
    main()