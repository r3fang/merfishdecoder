import os
import pickle
import pandas as pd
import numpy as np
import random 

from merfishdecoder.core import dataset
from merfishdecoder.util import utilities
from merfishdecoder.util import barcoder

def run_job(dataSetName: str = None,
            decodedBarcodesName: list = None,
            outputName: str = None):
    
    """
    Export barcodes.

    Args
    ----
    dataSetName: input dataset name.
    
    decodedBarcodesName: a list of decoded barcode file names.

    outputName: output file that contains decoded barcodes. 
    
    """
    
    # dataSetName = "20200303_hMTG_V11_4000gene_best_sample/data/"
    # decodedBarcodesName = "decodedBarcodes"
    # outputName = "exportedBarcodes/barcodes.h5"
    
    utilities.print_checkpoint("Export Barcodes")
    utilities.print_checkpoint("Start")
    
    # generate zplane object
    dataSet = dataset.MERFISHDataSet(
        dataDirectoryName = dataSetName);

    # change to work directory
    os.chdir(dataSet.analysisPath)
    
    # create the folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)
    
    # export barcodes
    barcodes = barcoder.export_barcodes(
            obj = dataSet,
            fnames = decodedBarcodesName);

    # save barcodes per fov
    for fov in np.unique(barcodes.fov):
        barcodes[barcodes.fov == fov].to_hdf(
            outputName,
            key = "fov_%d" % fov);

    utilities.print_checkpoint("Done")

