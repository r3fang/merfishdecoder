import os
import pickle
import pandas as pd
import numpy as np

from merfishdecoder.core import zplane
from merfishdecoder.util import utilities
from merfishdecoder.util import barcoder
from merfishdecoder.util import decoder

def run_job(dataSetName: str = None,
            fov: int = None,
            zpos: float = None,
            decodedImagesName: str = None,
            outputName: str = None,
            psmName: str = None,
            barcodesPerCore: int = 10,
            maxCores: int = 10):
    
    """
    Extract barcodes from decoded images.

    Args
    ----
    dataSetName: input dataset name.
    
    inputFile: input movie for decoding.

    outputFile: output file that contains decoded barcodes. 
    
    psmName: pixel scoring model file name.
             
    maxCores: number of cores for parall processing.
             
    """
    
    # dataSetName = "MERFISH_test/data/"
    # fov = 0
    # zpos = 1.0
    # decodedImagesName = "decodedImages/fov_0_zpos_1.0.npz"
    # outputName = "decodedBarcodes/fov_0_zpos_1.0.h5"
    # psmName = "pixel_score_machine.pkl"
    # barcodesPerCore = 10
    # maxCores = 10

    utilities.print_checkpoint("Extract Barcodes")
    utilities.print_checkpoint("Start")
    
    # generate zplane object
    zp = zplane.Zplane(dataSetName,
                       fov=fov,
                       zpos=zpos)

    # create the folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)
    
    # load the score machine
    psm = pickle.load(open(psmName, "rb"))
    
    # load decoding movie
    f = np.load(decodedImagesName)
    decodes = {
        "decodedImage": f["decodedImage"],
        "magnitudeImage": f["magnitudeImage"],
        "distanceImage": f["distanceImage"]
    }
    f.close()
    
    # calculate pixel probability
    decodes["probabilityImage"] = \
        decoder.calc_pixel_probability(
            model = psm,
            decodedImage = decodes["decodedImage"],
            magnitudeImage = decodes["magnitudeImage"],
            distanceImage = decodes["distanceImage"],
            minProbability = 0.01)
    
    # extract barcodes
    barcodes = barcoder.extract_barcodes(
        decodedImage = decodes["decodedImage"],
        distanceImage = decodes["distanceImage"],
        probabilityImage = decodes["probabilityImage"],
        magnitudeImage = decodes["magnitudeImage"],
        barcodesPerCore = barcodesPerCore,
        numCores = maxCores)
    
    # add fov and zpos info
    barcodes = barcodes.assign(fov = fov) 
    barcodes = barcodes.assign(global_z = zpos) 
    barcodes = barcodes.assign(z = \
        zp._dataSet.get_z_positions().index(zpos))
    
    # save barcodes
    barcodes.to_hdf(outputName,
                    key = "barcodes")
    
    utilities.print_checkpoint("Done")
    
