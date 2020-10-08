import os
import pickle
import pandas as pd
import numpy as np
import random 
import h5py

from merfishdecoder.core import dataset
from merfishdecoder.util import utilities
from merfishdecoder.util import barcoder

def run_job(dataSetName: str = None,
            exportedBarcodesName: str = None,
            outputName: str = None,
            fovNum=20,
            misIdentificationRate: float = 0.05,
            keepBlankBarcodes: bool = True,
            minAreaSize: int = 1):

    """
    Export barcodes.

    Args
    ----
    dataSetName: input dataset name.
    
    decodedBarcodesName: a list of decoded barcode file names.

    outputName: output file that contains decoded barcodes. 
    
    """
    
    utilities.print_checkpoint("Filter Barcodes")
    utilities.print_checkpoint("Start")
    
    # generate MERFISH dataset object
    dataSet = dataset.MERFISHDataSet(
        dataDirectoryName = dataSetName);

    # change to work directory
    os.chdir(dataSet.analysisPath)
    
    # create output folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)
    
    # randomly sample fovNum barcodes
    f = h5py.File(exportedBarcodesName, 'r')
    fovs = list(f.keys())
    f.close()
    barcodes = pd.concat([ 
        pd.read_hdf(exportedBarcodesName, key = key)
        for key in random.sample(fovs, min(len(fovs), fovNum)) ],
        ignore_index = True)
    
    # estimate likelihood cutoff
    likelihoodThreshold = \
        barcoder.estimate_barcode_threshold(
            barcodes = barcodes,
            codebook = dataSet.get_codebook(),
            cutoff = misIdentificationRate,
            bins = 200);
    
    # filter barcodes
    for fov in fovs:
        barcodes = pd.read_hdf(exportedBarcodesName, 
                               key=fov)
        
        barcodes = barcoder.filter_barcodes(
            barcodes,
            dataSet.get_codebook(),
            likelihoodThreshold=likelihoodThreshold,
            keepBlankBarcodes=keepBlankBarcodes,
            minAreaSize=minAreaSize)
        
        barcodes.to_hdf(
            outputName,
            key = fov);

    utilities.print_checkpoint("Done")
