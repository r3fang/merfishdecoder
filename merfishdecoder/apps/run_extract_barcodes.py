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
            barcodesPerCore: int = 5,
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
            
    # print input variables
    print("====== input ======")
    print("dataSetName: %s" % dataSetName)
    print("fov: %d" % fov)
    print("zpos: %f" % zpos)
    print("decodedImagesName: %s" % decodedImagesName)
    print("outputName: %s" % outputName)
    print("barcodesPerCore: %s" % barcodesPerCore)
    print("maxCores: %s" % maxCores)
    print("==================\n")
    
    utilities.print_checkpoint("Extract Barcodes")
    utilities.print_checkpoint("Start")
    
    # generate zplane object
    zp = zplane.Zplane(dataSetName,
                       fov=fov,
                       zpos=zpos)

    # create the folder
    os.makedirs(os.path.dirname(outputName),
                exist_ok=True)

    # load decoding movie
    f = np.load(decodedImagesName)
    decodes = {
        "decodedImage": f["decodedImage"],
        "magnitudeImage": f["magnitudeImage"],
        "distanceImage": f["distanceImage"]
    }
    f.close()
        
    # load the score machine
    if psmName != None:
        psm = pickle.load(open(psmName, "rb"))
        # calculate pixel probability
        decodes["probabilityImage"] = \
            decoder.calc_pixel_probability(
                model = psm,
                decodedImage = decodes["decodedImage"],
                magnitudeImage = decodes["magnitudeImage"],
                distanceImage = decodes["distanceImage"],
                minProbability = 0.01)
    else:
        decodes["probabilityImage"] = \
            decodes["distanceImage"]

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
    
def main():
    dataSetName = "190528_LPCDH1_DIV18_Map2TauAnkG"
    fov = 76
    zpos = 11.0
    decodedImagesName = \
        "decodedImages/fov_{fov:d}_zpos_{zpos:.1f}.npz".format(
            fov = fov, zpos = zpos)
    outputName = \
        "extractedBarcodes/fov_{fov:d}_zpos_{zpos:.1f}.h5".format(
            fov = fov, zpos = zpos)
    psmName = None
    barcodesPerCore = 1
    maxCores = 10

    run_job(dataSetName = dataSetName,
            fov = fov,
            zpos = zpos,
            decodedImagesName = decodedImagesName,
            outputName = outputName,
            psmName = psmName,
            barcodesPerCore = barcodesPerCore,
            maxCores = maxCores)
