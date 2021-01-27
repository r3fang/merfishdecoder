import os
import pickle
import pandas as pd
import numpy as np
import multiprocessing as mp
import geopandas as geo
import sys
from shapely.geometry import Point, Polygon

from merfishdecoder.util import utilities
from merfishdecoder.core import dataset

def read_barcodes_per_fov(
    fname: str = None,
    fov: int = None):
    try:
        return pd.concat([
            pd.read_hdf(fname, key="fov_%d" % fov) ],
            axis=1)
    except KeyError:
        print("barcodes in fov_%d does not exist" % fov)
        return None

def assign_barcodes_per_fov(
    barcodeFileName: str = None,
    features: geo.geodataframe.GeoDataFrame = None,
    fov: int = None
    ) -> pd.DataFrame:

    """
    Assign barcodes to feature for each FOV.
    """

    # read barcodes from one FOV
    bd = read_barcodes_per_fov(
        fname = barcodeFileName,
        fov = fov)

    if bd is None:
        return None
    
    # extract features belong to one fov
    ft = features[features.fov == fov].reset_index()

    # assign barcodes to segments
    bd = bd.assign(feature_name = "NA")
    if ft.shape[0] > 0:
        for i, s in ft.iterrows():
            bdz = bd
            if bdz.shape[0] > 0:
                idxes = np.array([j for (x, y, j) in
                    zip(bdz["global_x"],
                        bdz["global_y"],
                        bdz.index) \
                        if Point(x,y).within(s.geometry)])
                if len(idxes) > 0:
                    bd.loc[idxes,"feature_name"] = s["name"]
    return bd

def main():

    """
    Assign barcode to features.

    Args
    ----
    dataSetName: input dataset name.
    
    exportedBarcodesName: exported barcode file name in .h5 format. 

    exportedFeaturesName: exported feature file name in .shp format.
    
    outputName: output file name.
    
    maxCores: max number of processors for parallel computing. 
    
    """
    
    dataSetName = sys.argv[1]
    exportedFeaturesName = "exportedFeatures/dendrite.shp"
    
    # generate MERFISH dataset object
    dataSet = dataset.MERFISHDataSet(
            dataSetName)
    
    # change to work directory
    os.chdir(dataSet.analysisPath)
    
    # read features
    features = geo.read_file(
        exportedFeaturesName)
    
    features = features.assign(name= ["fov_%d_feature_%d" % (int(fov), x) \
        for (fov, x) in zip(features.fov, features.idx)])
    
    features.to_file(
        filename = "exportedFeatures/dendrite.shp")

if __name__ == "__main__":
    main()
    