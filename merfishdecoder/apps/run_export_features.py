import os
import geopandas as geo
import pandas as pd
import numpy as np
import multiprocessing as mp

from merfishdecoder.core import dataset
from merfishdecoder.util import utilities
from merfishdecoder.util import segmentation
    
def FileCheck(fn):
	try:
		geo.read_file(fn)
		return True
	except:
		return False

def run_job(
    dataSetName: str = None,
    outputName: str = None,
    segmentedFeaturesName: list = None,
    bufferSize: int = 15):
    
    """
    Extract features from decoded images for each fov.

    Args
    ----
    dataSetName: input dataset name.

    fov: the field of view to be processed.
    
    outputName: output file name for segmented images.
    
    """
    
    # dataSetName = "MERFISH_test/data"
    # segmentedFeaturesName = "extractedFeatures"
    # outputName = "exportedFeatures/DAPI"
    
    # check points
    utilities.print_checkpoint("Export Features")
    utilities.print_checkpoint("Start")
    
    # create merfish dataset
    dataSet = dataset.MERFISHDataSet(
        dataSetName)

    # change to working directory
    os.chdir(dataSet.analysisPath)

    # create output folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)


    # check file formats first and remove empty files
    segmentedFeaturesNameValid = \
        [ x for x in segmentedFeaturesName if FileCheck(x) ]
    
    # load all the segmented features
    features = pd.concat([ 
            geo.read_file(f) for f in segmentedFeaturesNameValid], 
        ignore_index=True)

    # connect features per fov
    features = pd.concat([ 
        segmentation.connect_features_per_fov(
            dataSet = dataSet,
            features = features,
            fov = fov,
            bufferSize = bufferSize) \
            for fov in np.unique(features.fov) ],
        ignore_index = True)
    
    # global alingment
    features = pd.concat([ 
        segmentation.global_align_features_per_fov(
            dataSet = dataSet,
            features = features,
            fov = fov) \
            for fov in np.unique(features.fov) ],
        ignore_index = True)

    if not features.empty:
        features[['fov', 'x', 'y', 'z', 'global_x', 
            'global_y', 'global_z', 'name', 
            'geometry']].to_file(
            filename = outputName)

    utilities.print_checkpoint("Done")


